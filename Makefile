.PHONY: build run test clean
build:
	nix develop --command cargo build --release
run: build
	./target/release/*
test:
	nix develop --command cargo test
clean:
	nix develop --command cargo clean
