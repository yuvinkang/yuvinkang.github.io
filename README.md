# My personal website

Live at <https://yuvinkang.github.io>. GitHub builds the site itself — there is
nothing to install and nothing to run. Commit a change and it is live in about a
minute.

## Adding a photo

Two steps every time.

**1. Upload the file.** On GitHub, open the folder it belongs in, then
**Add file → Upload files → Commit changes**.

**2. Point the site at it.** Open the matching file below, click the pencil
icon, change the path, commit.

A path always starts with `/assets/images/…`, exactly matching the file name you
uploaded, capital letters included.

### Where each photo goes

| What you want to change | Upload to | Then edit |
| --- | --- | --- |
| Ferris wheel on the landing page | `assets/images/gallery/` | `_data/gallery.yml` → `src:` |
| Hover photos in Personal | `assets/images/personal/` | `_data/personal.yml` → `image:` |
| School logos in Profile | `assets/images/logos/` | `_data/profile.yml` → `logo:` |
| Cover photo on a project page | `assets/images/projects/<project>/` | that project's file in `_projects/` → `image:` |
| Banner across the top of a project page | `assets/images/projects/<project>/` | the project's layout in `_layouts/` (`px-hero-img`) |
| Photo inside a blog post | `assets/images/posts/` | the post in `_posts/`, as `![description](/assets/images/posts/name.jpg)` |

Example — swapping the first Ferris-wheel photo. Upload `orchestra.jpg` to
`assets/images/gallery/`, then in `_data/gallery.yml`:

```yaml
- src: /assets/images/gallery/orchestra.jpg
  caption: "Yale Symphony Orchestra"
  blurb: "Principal bassist, Yale Symphony Orchestra."
```

`caption` is the title shown when the photo is opened; `blurb` is what the
stickman riding that cabin says on hover.

To take a photo away rather than replace it: in `_data/personal.yml` set
`image: ""`; in `_data/gallery.yml` delete the three lines of that entry.

### What to upload

- **JPG** for photographs, **PNG** for logos and anything with a transparent
  background, **WEBP** if you already have it.
- Resize to about **1600px** on the long side first. Phone photos are three or
  four times that, which only makes the page slow to load.
- Lower-case file names, hyphens instead of spaces: `club-soccer.jpg`, not
  `Club Soccer.JPG`.
- The `.svg` files sitting in those folders now are placeholders. Replacing
  them is the point — they are not needed afterwards.

### If a photo does not show up

Nearly always the path. Check the file name matches character for character,
that it starts with `/assets/`, and that the file really did commit (open its
folder on GitHub and look). Then hard-refresh the page: **Ctrl/Cmd + Shift + R**.

## Adding a file to download — a PDF, a CV, a CAD model

Same two steps as a photo, with one extra rule: the link text has to live
somewhere that accepts a link.

**1. Upload it to `assets/files/`.** That folder already holds the biolistics
paper and the two STEP models.

**2. Link to it.** Where depends on the page:

- **In any prose** — a project write-up in `_projects/`, a blog post in
  `_posts/`, a `text:` or `summary:` field in `_data/` — write it as Markdown:

  ```markdown
  [Read the paper (PDF)](/assets/files/biolistics-paper.pdf)
  ```

  Keep the leading `/`. The text in square brackets is what people see.

- **On the biolistics page**, there is a button already wired up. Set
  `paper:` in `_projects/biolistic-optimization.md` to the file's path and the
  button appears; leave it empty and it does not.

- **In the facts row of a project page** (where "STEP file ↓" sits on the
  shower chair and the dispenser), the link is in that page's layout in
  `_layouts/`. Copy the line that is already there and change the file name.

### Linking your résumé from the landing page

Upload `resume.pdf` to `assets/files/`, then in `_config.yml` fill in the
`resume:` line that is already there:

```yaml
resume: "/assets/files/resume.pdf"
```

A **Résumé** button appears next to Email and LinkedIn on the landing page.
Leave it as `""` and the button stays hidden.

### Notes

- Keep PDFs under about 10 MB; anything larger is slow to open on a phone.
- Lower-case names, hyphens instead of spaces: `yuvin-kang-cv.pdf`.
- Replacing a file but keeping the same name means every existing link keeps
  working — that is the easy way to update a CV.
- Anything in `assets/` is public to anyone with the link, the same as the rest
  of the site.

## Everything else

Text lives in `_data/*.yml` and `_projects/*.md`. Each file opens with a comment
explaining what its fields do. `CLAUDE.md` is notes for Claude, not for the
site; it never appears on the page.
