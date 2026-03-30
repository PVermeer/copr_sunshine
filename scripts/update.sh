#!/bin/bash

# Custom updater for sunshine so it can be used with rpm-tools
# Status is exported to $XDG_RUNTIME_DIR/update-vars

set -e
set -o pipefail

if [ "$CI" = "true" ]; then
  source ../rpm-tools/scripts/bash-color.sh
else
  # shellcheck source=../rpm-tools/scripts/bash-color.sh
  source ./rpm-tools/scripts/bash-color.sh
fi

release_type=$1
if [ ! "$release_type" = "stable" ] && [ ! "$release_type" = "beta" ] && [ ! "$release_type" = "all" ]; then
  echo_error "Please add parameter \"stable\", \"beta\" or \"all\""
  exit 1
fi

TEMP_DIR=$XDG_RUNTIME_DIR
if [ -z "$TEMP_DIR" ]; then
  TEMP_DIR="/tmp"
fi
mkdir -p "$TEMP_DIR/copr_sunshine"
TEMP_DIR="$TEMP_DIR/copr_sunshine"
export RPM_SPEC_UPDATE="false"

get_global_vars_from_spec() {
  local spec_file=$1
  grep '^%global\s.*$' "$spec_file" | awk '{ print $2"="$3 }'
}

get_key() {
  echo "$1" | awk -F '=' '{ print $1 }'
}
get_value() {
  echo "$1" | awk -F '=' '{ print $2 }'
}

get_repo_url_from_spec() {
  local spec_file=$1
  local sourcerepo_keyvalue
  local url

  sourcerepo_keyvalue=$(grep '^%global sourcerepo\s.*$' "$spec_file" | awk '{ print $2"="$3 }')
  url=$(get_value "$sourcerepo_keyvalue")

  echo "$url"
}

get_tag_by_release() {
  local repo
  local tag_type
  local tag

  repo=$1
  tag_type=$2

  if [ "$tag_type" = "stable" ]; then
    tag=$(curl -s https://api.github.com/repos/LizardByte/Sunshine/releases/latest |
      jq -r .tag_name)
  elif [ "$tag_type" = "beta" ]; then
    tag=$(git ls-remote --tags "$repo" |
      awk -F/ '{print $3}' |
      sort -V |
      tail -n 1)
  fi

  if [ -z "$tag" ]; then
    echo "Failed to get latest tag or there are no tags"
    return 1
  fi

  echo "$tag"
}

get_commit_from_tag() {
  local repo
  local tag

  repo=$1
  tag=$2

  commit=$(git ls-remote --tags https://github.com/LizardByte/Sunshine |
    grep "refs/tags/$tag$" |
    cut -f1) || return 1

  if [ -z "$commit" ]; then
    echo "Failed to get latest tag or there are no tags"
    return 1
  fi

  echo "$commit"
}

update_spec_file() {
  local input_spec_file
  local output_spec_file
  local release_type
  local global_spec_vars
  local repo_url
  local release_tag

  input_spec_file=$1
  output_spec_file=$2
  release_type=$3

  global_spec_vars=$(get_global_vars_from_spec "$input_spec_file")
  repo_url=$(get_repo_url_from_spec "$output_spec_file")
  release_tag=$(get_tag_by_release "$repo_url" "$release_type")

  echo ""
  echo "Looking for remote changes for $release_type"

  local keyValue
  for keyValue in $global_spec_vars; do
    local key
    local value
    key=$(get_key "$keyValue")
    value=$(get_value "$keyValue")

    if [ "$key" = "version" ]; then
      local current_version
      local new_version

      current_version=$value
      new_version=${release_tag#v}

      echo ""
      echo_color -n "$key:"
      echo " $current_version -> $new_version"

      if [ "$current_version" = "$new_version" ]; then
        echo_success "No version change detected for $release_type"
      else
        echo_warning "Version change detected for $release_type"
        RPM_SPEC_UPDATE="true"
      fi

      sed -i "s/%global\s$key\s.*/%global $key $new_version/" "./${output_spec_file}"
    fi

    if [ "$key" = "commit" ]; then
      local current_commit
      local new_commit

      current_commit=$value
      new_commit=$(get_commit_from_tag "$repo_url" "$release_tag")

      echo_color -n "$key:"
      echo " $current_commit -> $new_commit"

      if [ "$current_commit" = "$new_commit" ]; then
        echo_success "No commit change detected for $release_type"
      else
        echo_warning "Commit change detected for $release_type"
        RPM_SPEC_UPDATE="true"
      fi

      sed -i "s/%global\s$key\s.*/%global $key $new_commit/" "./${output_spec_file}"
    fi

    if [ "$key" = "releasetype" ]; then
      sed -i "s/%global\s$key\s.*/%global $key $release_type/" "./${output_spec_file}"
    fi

    if [ "$key" = "tag" ]; then
      sed -i "s/%global\s$key\s.*/%global $key $release_tag/" "./${output_spec_file}"
    fi
  done

  if [ "$RPM_SPEC_UPDATE" = "true" ]; then
    echo ""
    echo_success "Updated: $output_spec_file"
  fi
}

update_rpm_releases=("$release_type")
if [ "$release_type" = "all" ]; then
  update_rpm_releases=("stable" "beta")
fi

for release_type in "${update_rpm_releases[@]}"; do

  echo_color "\n=== Update RPM for $release_type ==="

  spec_file=""
  if [ "$release_type" = "stable" ]; then
    spec_file="./sunshine.spec"
  elif [ "$release_type" = "beta" ]; then
    spec_file="./sunshine-beta.spec"
  fi

  cp "$spec_file" "$TEMP_DIR"
  current_spec_file="$TEMP_DIR/$spec_file"
  cp "./sunshine-in.spec" "$spec_file"
  update_spec_file "$current_spec_file" "$spec_file" "$release_type"

  # Check
  global_spec_vars=$(get_global_vars_from_spec "$spec_file")
  for keyValue in $global_spec_vars; do
    value=$(get_value "$keyValue")
    if [ "$value" = "0" ]; then
      # Redo if zero, dirty fix for new keys
      echo_warning "Global variables have been added to in spec, re-running update"
      cp "$spec_file" "$TEMP_DIR"
      update_spec_file "$current_spec_file" "$spec_file" "$release_type"
      break
    fi
  done

  # Update status for rpm-tools
  echo ""
  echo_color "=== Exporting status ==="
  status_file="$XDG_RUNTIME_DIR/update-vars"
  echo "Writing status to $status_file"

  touch "$status_file"
  echo "RPM_SPEC_UPDATE=$RPM_SPEC_UPDATE" >"$status_file"

  echo ""
  echo_success "Wrote to status file >> $status_file:"
  cat "$status_file"
  echo ""

done
