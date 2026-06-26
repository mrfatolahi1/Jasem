# jasem wiki — source

This folder holds the source Markdown for the [jasem GitHub
wiki](https://github.com/mrfatolahi1/jasem/wiki). A GitHub wiki is itself a git
repository (`<repo>.wiki.git`), so publishing is just a matter of copying these
files into that repo and pushing.

> **Why keep the source here?** The wiki lives in a *separate* git repo that
> isn't part of your normal clone. Keeping the pages under `wiki/` in the main
> repo means they're versioned alongside the code and reviewable in PRs; the
> `publish.sh` script syncs them to the live wiki.

## Pages

| File | Wiki page |
|------|-----------|
| `Home.md` | landing page (required name) |
| `_Sidebar.md` | the navigation sidebar (required name) |
| `_Footer.md` | the page footer (required name) |
| `Installation.md` … `FAQ.md` | one page each |

GitHub maps a filename to a page title by replacing hyphens with spaces, so
`Time-Tracking.md` becomes the page **"Time Tracking"**, linked as
`[[Time Tracking]]`.

## Publish (one-time setup)

A wiki repo only exists once the wiki has **at least one page**. So the very first
time:

1. On GitHub, open **`mrfatolahi1/jasem` → Settings → Features** and tick
   **Wikis** (if it isn't already).
2. Go to the **Wiki** tab and click **Create the first page**, type anything,
   and **Save**. This initialises `jasem.wiki.git` so it can be cloned/pushed.

## Publish (every time)

From this `wiki/` folder:

```sh
./publish.sh
```

The script clones the wiki repo, copies every `*.md` here into it, commits, and
pushes. Re-run it whenever you edit a page. See the script for the exact steps —
or do it by hand:

```sh
git clone https://github.com/mrfatolahi1/jasem.wiki.git /tmp/jasem.wiki
cp *.md /tmp/jasem.wiki/
cd /tmp/jasem.wiki
git add .
git commit -m "Update wiki"
git push
```

Your changes appear at <https://github.com/mrfatolahi1/jasem/wiki> immediately.

## Linking between pages

Use `[[Page Title]]` for an internal wiki link, or `[[Custom text|Page-Title]]`
to change the label. External links use normal Markdown. GitHub renders
GitHub-flavoured Markdown, so tables, fenced code, and task lists all work.
