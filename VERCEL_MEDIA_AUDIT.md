# Vercel media audit

The following persistent upload fields currently use Django's local file
storage. They cannot safely write to a Vercel Function filesystem in
production.

| Area | Model field | Upload path | Affected feature |
| --- | --- | --- | --- |
| Contracts | `Contract.pdf_file` | `contracts/` | Signed contract PDFs |
| Finance reports | report `pdf_file` | `reports/%Y/%m/` | Generated/stored finance reports |
| Library | `LibraryItem.file` | dynamic library path | Learning-library files |
| Marketplace | company `logo` | `companies/logos/` | Company branding |
| Marketplace | course `image` | `courses/images/` | Course catalogue images |
| Homework | task attachment | dynamic homework path | Teacher task attachments |
| Homework | submission `file` | dynamic homework path | Student homework uploads |
| Homework | related attachment `file` | dynamic homework path | Homework-related files |

All eight fields are user-visible features. Existing database file names may be
preserved, but the corresponding objects must be copied from the current
`media/` directory to an external object store before switching storage.

Recommended next step: choose an S3-compatible provider (for example Vercel
Blob, Cloudflare R2, or AWS S3), add its credentials only in Vercel environment
variables, configure a production-only Django storage backend, then copy media
objects and verify every stored URL. No storage backend was changed here because
no provider, bucket, or media-copy authorization was supplied.
