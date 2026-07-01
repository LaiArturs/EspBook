# [READ HERE](https://espbook.laiarturs.com/)

This poject is published as hugo static website.

## Seting up on Kubuntu 24.04

### 1. Install latest version of `hugo`
```sh
sudo snap install hugo --channel=extended
```

## Running development server

```sh
hugo server
```

Development preview of website should be available in: http://localhost:1313/

## Extrnding content

```sh
# Create a directory for Chapter 1
mkdir -p content/docs/chapter-1

# Create the chapter index file
hugo new content docs/chapter-1/_index.md

# Create a section inside Chapter 1
hugo new content docs/chapter-1/section-1.md
```

## Formatting Content

To ensure consistent dialogue spacing (blank lines before and after dialogue 
lines) and line lengths (wrapped at 80 characters) across all book chapters,
run the formatting script:

```sh
python3 scripts/format_book.py
```
