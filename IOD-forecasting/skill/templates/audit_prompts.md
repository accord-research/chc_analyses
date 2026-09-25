# Audit prompts

Two audits, in this order, every issuance. Spawn each as a subagent so it reads the work
cold rather than inheriting the author's assumptions.

---

## 1. Scientific and code audit

> You are auditing the IOD outlook in `experiments/IOD-forecasting`. Be adversarial and
> specific. Do not accept claims at face value — verify against the code and data.
>
> Read `iod_pipeline.py`, `refresh_outputs.py`, `report/IOD_outlook_<init>.md`, and the
> `outputs/*_<init>.*` files. Python is at
> `/opt/homebrew/Caskroom/miniforge/base/envs/accord-chc/bin/python`; run from the
> `IOD-forecasting` directory. Network fetches are slow — prefer cached outputs.
>
> Answer these:
> - **Leakage.** Is there any path by which information dated after a forecast's
>   initialisation reaches it? Consider the model fit, the day-of-year climatology, the
>   verification values, and every hyperparameter. For any correction applied to remove
>   leakage, is the correction itself clean, or does it introduce a second distortion?
> - **Like-for-like.** Where two methods are compared, are they scored on the same years
>   with the same information available to each? Name which is advantaged, in which
>   direction, and by how much.
> - **Every numeric claim** in the report, reconciled against the file that produced it,
>   rounding included. Give the correct value for any that does not reconcile.
> - **Claims about our own record** across issuances. Check each against every
>   `outputs/indices_*.csv` and against `README.md`.
> - **Reproducibility.** Is any reported number not emitted by `refresh_outputs.py` or
>   `refresh_alternatives()`?
> - **Statistical honesty.** Any claim stronger than its n supports; any bolded "winner"
>   whose margin is not resolvable; any coefficient asserted unstable without a standard
>   error.
>
> Do not edit files. Rank findings by severity. For each give the file and line or the
> exact sentence, what is wrong, why it matters, and the correct value or statement.
> Separate (i) definite errors, (ii) defensible but debatable, (iii) style. If something
> checks out, say so in one line rather than padding.

**Then:** verify the substantive findings yourself before acting. An auditor's mechanism can
be correct while its magnitude is overstated. Fix the code, not only the sentence. Where you
disagree, say so with the reason.

---

## 2. Stylistic audit (after the scientific fixes are in)

> You are performing a LANGUAGE-ONLY audit of `report/IOD_outlook_<init>.md`. Do not check
> numbers, methods, or code — those have been audited separately. Your only concern is
> wording.
>
> The standard: facts only, every sentence a measurement, a method, or a limitation. Terse,
> simple, scientific, professional. Highly measured and modest. No overstatement. No
> dramatic flourish in prose or in section titles. No writerly summarising line at the end
> of a section. No hedging so heavy it obscures meaning — one hedge, not two — except that
> the construction "x may imply that y may overstate z" is required where a finding suggests
> earlier work was weaker than implied; flag it only where it is doing no such work. Where
> findings qualify earlier work it must read as a qualification, never a retraction, and
> must never assert that previous work was wrong.
>
> Go through the document in order. For each shortfall give the verbatim sentence, what is
> wrong (overstatement / flourish / vagueness / stacked hedging / editorialising / register
> slip / redundancy / a title that editorialises), and a full concrete replacement, shorter
> where possible.
>
> Watch for these in particular.
> - Section titles that editorialise, and the Abstract, which is the likeliest site of
>   overstatement.
> - Emphasis adverbs that add no information, and bold used for emphasis rather than to
>   locate a figure.
> - Interpretive framings asserted as fact, such as "the durable finding" or "the
>   substantive development".
> - Verbatim or third-occurrence repetition of a caution.
> - **Compressed epigrams.** Brevity is not the test. A short stylish line such as "With the
>   east near zero, the dipole is the western anomaly" or "Two cautions apply." is a
>   stylistic device and fails the standard however few words it uses. Flag every one.
> - **Semicolons and colons in prose.** Flag all of them. Replace with full sentences. A
>   `Label.` opening a bulleted limitation is the only acceptable use.
> - **Statistics used as shorthand.** "Two horizons clear zero" states nothing a reader can
>   use. Demand a replacement that says what was measured and against what.
> - **A Method section written as a specification sheet**, with bolded field labels and every
>   parameter listed. It should be short plain prose saying what was done.
>
> Do not edit the file. Return findings ordered by position. If a section is clean, say so
> in one line.

**Then:** apply the replacements, rebuild the PDF, and only then report the issuance as done.
