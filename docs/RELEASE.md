# Publication handoff

The release is prepared for [adrianghilardi/tfcg-charcoal-model](https://github.com/adrianghilardi/tfcg-charcoal-model) and Adrian Ghilardi's personal Zenodo account. Both are outside MoFuSS. The GitHub repository has been created; Zenodo identifiers are added only after verification. MIT code licensing and the choice of CC BY 4.0 for contributed data were authorized by Adrian Ghilardi on 17 September 2026.

## Files to preserve

- Versioned source repository, including the untouched supplied EGOML, tests, configurations, documentation and validation reports.
- `tfcg_case_data_v0.1.0.zip`: checksummed original analytical inputs and baseline tables, with licence notices.
- `tfcg_results_v0.1.0.zip`: 100-realization audit, 1,000-realization corrected experiments, native evidence and generated summaries.
- `SHA256SUMS.txt`: archive checksums. Retain the source commit identifier in the release metadata.

The manuscript and BibTeX are maintained separately in the paper workspace. They can be added to a publication archive after coauthor review. Do not invent ORCIDs, affiliations, funders or a manuscript DOI.

## Publish when the account is available

1. Push this local main branch to the confirmed personal repository. Use ordinary account authorization; never put access tokens into scripts, Git history, or release metadata.
2. Confirm the configured GitHub Actions checks succeed on Windows and Linux. Local verification does not establish remote CI success.
3. Create a Zenodo dataset record for the case-study bundle and numerical results. Use CC BY 4.0, the five authors in manuscript order, the specific version and the supplied description. Include the source commit and link the software record. Reserve a DOI if needed before finalizing documentation; do not cite a reserved DOI as a published accessible record.
4. Add the verified dataset DOI/download URL to README, manuscript availability statement and any integration test download step. Re-run the workflow using the public download and check its hash.
5. Link the GitHub repository to the chosen Zenodo account and create the software release. Inspect the resulting Zenodo record, archive contents, version DOI and licence. Alternatively upload the exact source archive manually. Follow the current [Zenodo release guide](https://help.zenodo.org/docs/github/archive-software/github-upload/).
6. Put the exact version DOIs, date and repository URL in `CITATION.cff`, the paper and the BibTeX file. Preserve the DOI for the particular analysed version; use a new version for later parameter/code changes.

The metadata templates in `config/` omit unknown identifiers. They are drafts, not proof of deposition. Verify the final record and its downloadable content before describing the archive as public.
