# Definitions
repository = tpesout
identifier = vgp_bionano
version = 0.0.0
git_commit ?= $(shell git log --pretty=oneline -n 1 | cut -f1 -d " ")
name = ${repository}/${identifier}
tag = ${version}--${git_commit}
solve_source_tarball = Solve3.3_10252018.tar.gz

# Steps
build:
	# do the docker build
	mkdir tmp
	cp -r ../../../pipeline/bionano/* ${solve_source_tarball} tmp
	docker build -t ${name}:${tag} .
	docker tag ${name}:${tag} ${name}:latest
	rm -r tmp

push: build
	# Requires ~/.dockercfg
	docker push ${name}:${tag}
	docker push ${name}:latest
