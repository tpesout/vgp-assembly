FROM tpesout/vgp_base:latest
MAINTAINER Trevor Pesout, tpesout@ucsc.edu

ENV YAK_CHECKOUT=6de3aff
ENV HIFIASM_CHECKOUT=v0.7
ENV GFATOOLS_CHECKOUT=v0.4

### Yak
WORKDIR /root/tools/
RUN git clone https://github.com/lh3/yak.git && \
    cd yak && \
    git fetch && \
    git checkout $YAK_CHECKOUT && \
    make && \
    ln -s yak /usr/local/bin/yak

### Hifiasm
WORKDIR /root/tools
RUN git clone https://github.com/chhylp123/hifiasm.git && \
    cd hifiasm && \
    git fetch && \
    git checkout $HIFIASM_CHECKOUT && \
    make && \
    ln -s hifiasm /usr/local/bin/hifiasm

### gfatools
WORKDIR /root/tools
RUN git clone https://github.com/lh3/gfatools.git && \
    cd gfatools && \
    git fetch && \
    git checkout $GFATOOLS_CHECKOUT && \
    make && \
    ln -s gfatools /usr/local/bin/gfatools

WORKDIR /data
