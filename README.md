## Seting up on Kubuntu 24.04

```sh
sudo snap install hugo --channel=extended
```

## Running development server

```sh
hugo server -D
```

## Extrnding content

```sh
# Create a directory for Chapter 1
mkdir -p content/docs/chapter-1

# Create the chapter index file
hugo new content docs/chapter-1/_index.md

# Create a section inside Chapter 1
hugo new content docs/chapter-1/section-1.md
```
