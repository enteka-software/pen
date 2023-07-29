# Pen

Pen is a CLI tool that allows you to run a local server to write and publish content for your Astro.js blogs.

### Setup

Pen requires a GitHub Access Token to get write and commit your content to a repository.

**The GitHub Access Token is only stored in a config file on your system**

1. Once you have installed Pen run the `auth` command, this will setup your config file:

```
pen auth <github-access-token>
```

2. Setup the repo you would like to write content for with:

```
pen setup GitHubUsername/RepoName
```

You can run the setup command multiple times to setup multiple repos.

### Usage

Once you have completed setup, you can start the server to start writing content with:

```
pen start
```

Navigate to http://localhost:8000 to view the writing UI.

### Helper Commands

- `pen config` will print your config file
- `pen reset` will clear your config file
