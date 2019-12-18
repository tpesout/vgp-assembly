FROM tpesout/vgp_base:latest
MAINTAINER Trevor Pesout, tpesout@ucsc.edu

### repeatmasker
# 4.1.0
WORKDIR /opt/repeatmasker
RUN wget http://www.repeatmasker.org/RepeatMasker-4.1.0.tar.gz && \
     tar -xvf RepeatMasker-4.1.0.tar.gz && \
     rm -r RepeatMasker-4.1.0.tar.gz && \
     mv RepeatMasker RepeatMasker-4.1.0 && \
     cd RepeatMasker-4.1.0/ && \
     git clone https://github.com/oushujun/LTR_retriever.git && cd LTR_retriever && git checkout 72960e84951c52ff289465eae8f1ff8b04f82e69 && cp bin/trf409.linux64 .. && cd .. && rm -rf LTR_retriever/ && chmod +x trf409.linux64  &&   mv trf409.linux64 /bin && \
     cpan Text::Soundex && \
     touch /opt/repeatmasker/RepeatMasker-4.1.0/util/maskFile.pl && \
     ./configure -trf_prgm /bin/trf409.linux64 -hmmer_dir /root/bin/hmmer_3.2.1 -default_search_engine hmmer && \
     ln -s /opt/repeatmasker/RepeatMasker-4.1.0 /root/bin/repeatmasker_4.1.0 && \
     mkdir /root/modules/repeatmasker && \
     echo "#%Module" >> /root/modules/repeatmasker/4.1.0 && \
     echo "append-path PATH /root/bin/repeatmasker_4.1.0" >> /root/modules/repeatmasker/4.1.0  && \
     echo "#%Module" >>/root/modules/repeatmasker/.modulerc && \
     echo "module-version /4.1.0 default" >>/root/modules/repeatmasker/.modulerc

# 4.0.7
WORKDIR /opt/repeatmasker
RUN wget http://www.repeatmasker.org/RepeatMasker-open-4-0-7.tar.gz && \
     tar -xvf RepeatMasker-open-4-0-7.tar.gz && \
     rm -r RepeatMasker-open-4-0-7.tar.gz && \
     mv RepeatMasker RepeatMasker-4.0.7 && \
     cd RepeatMasker-4.0.7/ && \
     cpan Text::Soundex && \
     touch /opt/repeatmasker/RepeatMasker-4.0.7/util/maskFile.pl && \
     printf '\n/bin/trf409.linux64\n4\n/root/bin/hmmer_3.2.1\ny\n5\n' | perl ./configure --re_exec_perl=/usr/bin/perl && \
     ln -s /opt/repeatmasker/RepeatMasker-4.0.7 /root/bin/repeatmasker_4.0.7 && \
     echo "#%Module" >> /root/modules/repeatmasker/4.0.7 && \
     echo "prepend-path PATH /root/bin/repeatmasker_4.0.7" >> /root/modules/repeatmasker/4.0.7 

#TODO actually install bionano

WORKDIR /root/scripts/bionano/
COPY tmp/*.sh ./

WORKDIR /root/config/bionano
COPY tmp/*.xml ./

WORKDIR /data
ENTRYPOINT ["bash", "-i", "/root/scripts/bionano/_docker_bionano.sh"]
