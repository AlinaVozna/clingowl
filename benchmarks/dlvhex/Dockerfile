# Stage 0: build the Racer reasoner (the DL-Plugin talks to it over TCP).
# Commercial RacerPro is gone; we build the open-source successor (BSD-3)
# with Clozure CL. build-racer.lisp also restores one dropped protocol
# command via Racer's server-hook extension point (no sources patched).
FROM ubuntu:16.04 AS racerbuild

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y wget git ca-certificates m4 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN wget -q https://github.com/Clozure/ccl/releases/download/v1.11.5/ccl-1.11.5-linuxx86.tar.gz && \
    tar -xzf ccl-1.11.5-linuxx86.tar.gz && \
    rm ccl-1.11.5-linuxx86.tar.gz

RUN git clone --depth 1 https://github.com/ha-mo-we/Racer.git

# Quicklisp provides Racer's Lisp dependencies (aserve, etc.)
RUN wget -q https://beta.quicklisp.org/quicklisp.lisp && \
    /opt/ccl/lx86cl64 -n -b -l quicklisp.lisp -e '(quicklisp-quickstart:install)' -e '(ccl:quit 0)' && \
    mkdir -p /root/quicklisp/local-projects && \
    ln -s /opt/Racer /root/quicklisp/local-projects/Racer

COPY build-racer.lisp /opt/build-racer.lisp

RUN /opt/ccl/lx86cl64 -n -b -l /opt/build-racer.lisp -e '(ccl:quit 0)'

# Main stage: DLVHEX 2.5.0 + DL-Plugin. DLVHEX is from 2014-2016 and no
# longer builds on modern systems, so everything is pinned to
# period-correct versions (Ubuntu 16.04, GCC 4.8, Boost 1.55).
FROM ubuntu:16.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential cmake git wget bison flex \
    autoconf automake libtool dos2unix pkg-config gawk \
    scons re2c \
    libbz2-dev zlib1g-dev python-dev libraptor2-dev libltdl-dev \
    libcurl4-gnutls-dev \
    gcc-4.8 g++-4.8 \
    && rm -rf /var/lib/apt/lists/*

# GCC 4.8 as default compiler: the whole stack must share the old C++ ABI.
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.8 100 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.8 100 && \
    update-alternatives --install /usr/bin/cpp cpp /usr/bin/cpp-4.8 100

WORKDIR /workspace

# Boost 1.55. program_options must be built explicitly (dlvhex links against
# it) and --layout=system gives the plain library names its configure expects.
RUN wget https://archives.boost.io/release/1.55.0/source/boost_1_55_0.tar.gz && \
    tar -xzf boost_1_55_0.tar.gz && \
    cd boost_1_55_0 && \
    ./bootstrap.sh --prefix=/usr/local && \
    ./b2 -j4 install --layout=system threading=multi variant=release \
        link=shared runtime-link=shared \
        --with-atomic --with-chrono --with-date_time --with-filesystem \
        --with-graph --with-iostreams --with-program_options --with-regex \
        --with-serialization --with-system --with-test --with-thread && \
    ldconfig && \
    cd .. && rm -rf boost_1_55_0*

# dlvhex2 engine, pinned to Release_2_5_0. Its old configure can't detect the
# Boost version; the boost_cv_* cache variables hand it the answers (standard
# autoconf mechanism, no patching).
RUN git clone --recursive https://github.com/hexhex/core.git dlvhex && \
    cd dlvhex && \
    git checkout Release_2_5_0 && \
    git submodule update --init --recursive || true && \
    find . -type f \( -name "*.sh" -o -name "*.ac" -o -name "*.am" \) -exec dos2unix {} + 2>/dev/null || true && \
    ./bootstrap.sh && \
    ./configure --with-boost=/usr/local \
        boost_cv_inc_path=/usr/local/include \
        boost_cv_lib_version=1_55 \
        CC=gcc-4.8 CXX=g++-4.8 \
        CPPFLAGS="-I/usr/local/include" \
        LDFLAGS="-L/usr/local/lib -Wl,-rpath,/usr/local/lib" && \
    make -j4 && \
    make install && \
    ldconfig

# raptor 1.x (required by the plugin, no longer packaged by Ubuntu). Its
# sources include <curl/types.h>, an empty header curl removed in 2011 --
# recreate it empty instead of patching raptor.
RUN apt-get update && apt-get install -y libxml2-dev && rm -rf /var/lib/apt/lists/* && \
    mkdir -p /usr/include/curl && touch /usr/include/curl/types.h && \
    wget https://download.librdf.org/source/raptor-1.4.21.tar.gz && \
    tar -xzf raptor-1.4.21.tar.gz && \
    cd raptor-1.4.21 && \
    ./configure --prefix=/usr/local && \
    make -j4 && \
    make install && \
    ldconfig && \
    cd .. && rm -rf raptor-1.4.21*

# DL-Plugin, pinned. Needs the RacerPro binary present at configure time
# (copied from stage 0). --recursive matters: bootstrap.sh is a symlink into
# a submodule.
COPY --from=racerbuild /usr/local/bin/RacerPro /usr/local/bin/RacerPro
RUN git clone --recursive https://github.com/hexhex/dlplugin.git && \
    cd dlplugin && \
    git checkout 44173707393553329204d882907ea0a888e4b5f0 && \
    git submodule update --init --recursive && \
    find . -type f \( -name "*.sh" -o -name "*.ac" -o -name "*.am" \) -exec dos2unix {} + 2>/dev/null || true && \
    ./bootstrap.sh && \
    ./configure --with-boost=/usr/local \
        boost_cv_inc_path=/usr/local/include \
        boost_cv_lib_version=1_55 \
        CC=gcc-4.8 CXX=g++-4.8 \
        CPPFLAGS="-I/usr/local/include" \
        LDFLAGS="-L/usr/local/lib -Wl,-rpath,/usr/local/lib" \
        PKG_CONFIG_PATH=/usr/local/lib/pkgconfig && \
    make -j4 && \
    make install && \
    ldconfig

# Benchmark scripts and ontologies, plus the `bench` entry point:
#   docker run --rm dlvhex250 bench snomed
COPY generate_hex.py bench.sh /opt/clingowl-bench/
COPY ontologies /opt/clingowl-bench/ontologies
RUN printf '#!/bin/sh\nexec sh /opt/clingowl-bench/bench.sh "$@"\n' > /usr/local/bin/bench && \
    chmod +x /usr/local/bin/bench /opt/clingowl-bench/bench.sh

CMD ["/bin/bash"]
