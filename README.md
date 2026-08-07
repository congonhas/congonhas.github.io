# flaviocunha.com

The website of Flávio Cunha, Ervin K. Zingler Chair of Economics, Rice University.

Built with [Quarto](https://quarto.org). Every paper on the site comes from one
file, `papers.bib`. Nothing else needs editing to add a paper.

---

## Adding a paper

1. Open **`papers.bib`**.
2. Copy the nearest existing entry, change the fields, save.
3. That is it. The site rebuilds itself and the paper appears on the research
   page, in the topic filters, in the BibTeX download, and, if you add
   `selected = {yes}`, on the homepage.

You can do all of this in your browser: open `papers.bib` on github.com, click
the pencil icon, edit, then click **Commit changes**. The live site updates about
a minute later. No software to install.

### Fields

Standard BibTeX, plus:

| Field | What it does |
|---|---|
| `category` | `wp` working paper, `pub` publication, `old` older working paper. Required. |
| `topics` | Comma-separated: `early`, `beliefs`, `meas`, `ineq`, `edu`. Drives the filters. |
| `selected` | `yes` puts it in **Selected research** on the homepage. |
| `status` | Free text tag, for example `Revise and resubmit, JPE`. |
| `nber` | NBER id (`w35370`) or a full URL. |
| `doi` | With or without the `https://doi.org/` prefix. |
| `pdf` | A PDF you host yourself, for example `papers/draft.pdf`. |
| `code` | Link to the replication package. |
| `summary` | Link to a policy brief or plain-language summary. |
| `venue` | Overrides the auto-built journal line, for awkward cases. |
| `sortyear` | Changes ordering only, not what is displayed. |

---

## What each file is for

```
papers.bib          every paper. The one file you will actually edit.
index.qmd           homepage text
research.qmd        research page (the list itself is generated)
teaching.qmd        course descriptions
build_papers.py     turns papers.bib into the HTML lists. Runs automatically.
styles.css          the entire design, about 200 lines
_header.html        name and navigation
_footer.html        footer, plus the day/night and filter scripts
_head.html          sets the theme before first paint, to avoid a white flash
fonts/              Bitstream Charter, self-hosted
papers/             PDFs you host yourself
_quarto.yml         site configuration
```

Files starting with `_research` or `_selected`, plus `bibtex/` and
`all-papers.bib`, are generated on every build and are not in version control.

---

## Design notes

**Typography.** Bitstream Charter at 17px over a 44rem measure, self-hosted in
four weights. There is deliberately no `local()` fallback: a visitor's own copy
of Charter may differ, and the point is that the site looks the same everywhere.
Navigation and link badges use the system sans stack so the interface never
competes with a paper title.

**Day and night.** White by default, dark gray between 19:00 and 07:00 in the
visitor's own time zone. If their operating system asks for dark mode, that wins
at any hour. The sun/moon control in the header overrides for the visit. To
change the hours, edit `DARK_FROM` and `DARK_UNTIL` in `_footer.html`.

**No framework.** Bootstrap is switched off (`theme: none`). The whole design is
`styles.css`, and the whole behaviour is about sixty lines of plain JavaScript in
`_footer.html`. There are no dependencies to update and nothing that can break on
its own.

---

## Running it locally (optional)

You do not need to. But if you want to preview before publishing:

```bash
quarto preview
```

That opens the site in a browser and reloads as you edit.

---

## Publishing

`.github/workflows/publish.yml` rebuilds and deploys on every push to `main`.
To trigger a rebuild without changing anything, go to the **Actions** tab and run
**Publish website**.

---

## Before going live at www.flaviocunha.com

- [ ] Add a real `cv.pdf`. The one in the repository is a placeholder.
- [ ] Decide on a homepage headshot. The layout supports one; there is none now.
- [ ] Copy the four older working paper PDFs out of the Wix file store into
      `papers/` and repoint them in `papers.bib`. Today they still load from Wix,
      so they break when that subscription lapses.
- [ ] Move the three replication packages off Dropbox to openICPSR or Harvard
      Dataverse, then add `code = {...}` to those three entries.
- [ ] Add redirects for the old Wix URLs: `/working-papers`, `/padin`,
      `/codes-and-data`, `/teaching`. These are the links people have bookmarked
      and cited.
- [ ] Add a `CNAME` file containing `www.flaviocunha.com` and list it under
      `resources` in `_quarto.yml`. Do this only once DNS is pointed, not before.
- [ ] Point DNS: four A records at the apex to 185.199.108.153, 185.199.109.153,
      185.199.110.153, 185.199.111.153, and a CNAME on `www` to
      `congonhas.github.io`. Leave MX records alone so email keeps working.

## Citation accuracy

Every citation in `papers.bib` was verified against Crossref, OpenAlex and
IDEAS/RePEc in August 2026. Ten entries differed from the previous website; each
correction is noted in a comment above the entry it applies to.

Abstracts are present for the NBER working papers, taken verbatim from NBER.
Journal articles do not have abstracts yet.
