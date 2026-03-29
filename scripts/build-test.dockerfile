ARG TAG="latest"
ARG USERNAME=test
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG WORK_DIR=/home/$USERNAME/build-test

FROM fedora:latest AS source
ARG WORK_DIR

RUN mkdir -p ${WORK_DIR}
WORKDIR ${WORK_DIR}

RUN dnf install -y git

RUN git clone https://github.com/PVermeer/rpm-tools.git
RUN git clone https://github.com/LizardByte/Sunshine.git

FROM fedora:${TAG} AS init
ARG WORK_DIR
ARG USERNAME
ARG USER_UID
ARG USER_GID

RUN sudo dnf update -y

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME
USER $USERNAME

RUN mkdir -p ${WORK_DIR}
WORKDIR ${WORK_DIR}

FROM init AS build-init
ARG WORK_DIR

RUN sudo dnf install -y which util-linux git jq rpmbuild rpmlint 
COPY ./.devcontainer/install-deps.sh .
RUN ./install-deps.sh

COPY --from=source ${WORK_DIR}/Sunshine ./Sunshine
COPY --from=source ${WORK_DIR}/rpm-tools ./rpm-tools

FROM build-init AS build
ARG SPEC_FILE

COPY  ${SPEC_FILE} ${SPEC_FILE}
RUN ./rpm-tools/rpm-tool build --spec-file="${SPEC_FILE}"

FROM init
ARG WORK_DIR

RUN sudo dnf install -y pkill

COPY --from=build ${WORK_DIR}/rpmbuild/RPMS/**/*.rpm ./
RUN sudo dnf install -y ./*.rpm

CMD [ "bash", "-c", "(sunshine &); sleep 5; pkill -INT sunshine;" ]
