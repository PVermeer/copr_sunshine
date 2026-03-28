#!/bin/bash

clean="false"
only_clean="false"
if [ -n "$1" ]; then
    if [ "$1" = "--clean" ]; then
        clean="true"
    elif [ "$1" = "--only-clean" ]; then
        only_clean="true"
        clean="true"
    else
        echo "Not a valid option"
        exit 1
    fi
fi

fedora_versions=("41" "42" "43" "44" "rawhide")
build_types=("stable ""beta")
docker_images=()
has_failed="false"
failed_versions=()

for version in "${fedora_versions[@]}"; do
    name="fedora-build-test-$version"

    for build_type in "${build_types[@]}"; do
        if [ "$only_clean" = "true" ]; then
            docker_images+=("$name")
            continue
        fi

        echo ""
        echo "==== Running docker test for Sunshine $build_type on Fedora $version ===="
        echo ""

        if [ "$build_type" = "stable" ]; then
            spec_file="./sunshine.spec"
        elif [ "$build_type" = "beta" ]; then
            spec_file="./sunshine-beta.spec"
        fi

        if ! docker build -f ./scripts/build-test.dockerfile \
            --build-arg TAG="$version" \
            --build-arg SPEC_FILE="$spec_file" \
            -t "$name" \
            .; then
            failed_versions+=("$version $build_type (build)")
            has_failed="true"
            continue
        fi
        if ! docker run --rm --device=/dev/dri "$name"; then
            failed_versions+=("$version $build_type (run)")
            has_failed="true"
        fi
        docker_images+=("$name")
    done
done

if [ "$clean" = "true" ]; then
    for image in "${docker_images[@]}"; do
        echo "Removing image $image"
        docker rmi "$image"
    done
    echo "Pruning docker cache"
    docker builder prune -f
fi

if [ "$has_failed" = "true" ]; then
    echo ""
    echo "======== FAILED ========"
    for failed_version in "${failed_versions[@]}"; do
        echo "Failed for Fedora $failed_version"
    done

    exit 1
fi

echo ""
echo "======== SUCCESS ========"
echo ""
