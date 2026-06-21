# ChatGPT Archive Builder

A local desktop tool for building and managing a personal ChatGPT conversation archive.

This project creates a static HTML archive from exported ChatGPT conversations. It is designed for people who want to keep their conversations organized locally, browse them by year/month/folder, search them, and customize how the archived conversations look.

The app is built with Python and CustomTkinter.

## What it does

ChatGPT Archive Builder can:

* Create a new archive structure
* Generate multiple year folders
* Generate all month folders for selected years
* Add custom folders
* Update conversation folders
* Apply a custom reading UI to exported conversation HTML files
* Search archived conversations by keywords
* Open search results directly
* Remember the saved archive root locally
* Customize the conversation UI
* Pick colors with a color picker
* Add custom user and assistant avatars
* Run a preflight check before sharing or publishing the project

## Archive structure

A generated archive can look like this:

```text
My Archive/
  index.html
  Conversations/
    index.html
    2024/
      index.html
      January 2024/
        index.html
      February 2024/
        index.html
    2025/
      index.html
      January 2025/
        index.html
  Projects/
    index.html
  Stories/
    index.html
```

The archive itself is static HTML. You can open it directly in a browser.

## How exported conversations are handled

This tool expects exported ChatGPT conversations as `.html` files.

The intended workflow is:

1. Export or save ChatGPT conversations as HTML files.
2. Place those files manually into the correct conversation folder, such as:

```text
Conversations/2026/June 2026/
```

3. Use **Update folder** in the app.
4. The app patches the conversation UI and updates the folder index.

The app does not try to guess where conversations belong. Manual placement keeps the archive predictable and avoids wrong auto-sorting.

## Customization

The app can generate a local conversation UI patch with custom settings such as:

* Background color
* Text color
* User bubble color
* Font size
* Line height
* Conversation width
* Message width
* Image width
* User avatar
* Assistant avatar

Custom settings are stored locally and are not meant to be committed to GitHub.

## Private local files

The following files are local/private and should not be committed:

```text
settings/settings.json
settings/generated_conversation_ui_patch.html
```

These may contain local paths, personal UI settings, or embedded avatar data.

They are ignored by `.gitignore`.

## Installation

Clone the repository, then install dependencies:

```bash
pip install -r requirements.txt
```

## Running the app

From the project root:

```bash
py run.py

## Running the preflight check

Before committing or sharing the project, run:

```bash
py tools/preflight_check.py
```

The preflight check verifies that required files exist, Python files compile, version numbers match, and private files are ignored.

Warnings about local settings files are normal as long as GitHub Desktop is not tracking those files.

## Version

Current version:

```text
0.0.9
```

## Project status

This project is in active development.

Current core features are working, but the project is still being cleaned and improved before public sharing.
