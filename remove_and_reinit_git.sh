#!/bin/bash
# Remove the .git directory, src, and tests directories, reinitialize git, and set up develop branch

if [ -d ".git" ]; then
  rm -rf .git
  echo ".git directory removed."
else
  echo "No .git directory found."
fi

if [ -d "src" ]; then
  rm -rf src
  echo "src directory removed."
else
  echo "No src directory found."
fi

if [ -d "tests" ]; then
  rm -rf tests
  echo "tests directory removed."
else
  echo "No tests directory found."
fi

git init

touch README.md
git add README.md
git commit -m "Initial commit"
git checkout -b develop
git branch

echo "Git repository reinitialized and switched to 'develop' branch." 