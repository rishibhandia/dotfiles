---
name: academic-review
description: Review scientific papers, grant proposals, and beamtime requests for clarity, structure, and persuasiveness. Evaluates from a reviewer's perspective for significance, approach, preliminary data, and broader impacts. Checks for common rejection mistakes. Use when polishing manuscripts, proposals, or any scientific writing before submission.
---

# Scientific Writing Review

Review scientific documents from a reviewer's perspective. Identify issues that lead to rejection and suggest improvements.

## Document Types

Detect and apply appropriate review criteria:
- **Scientific paper** → paper-checklist.md
- **Grant proposal (NSF/NIH)** → grant-checklist.md
- **Beamtime/facility request** → Hybrid (proposal structure + paper clarity)
- **Abstract only** → Condensed review focusing on completeness

## Review Workflow

### For Papers

1. **Fractal test**: Can reader understand at 1 min (abstract), 5 min (figures), 10 min (intro + first sentences)?
2. **Structure**: Does intro establish gap and significance? Does conclusion deliver on promises?
3. **Figures**: Check references/paper-checklist.md for complete list
4. **Style**: Active voice? Pronouns avoided? Acronyms minimized?
5. **References**: Properly formatted? No duplicates? Hyperlinks work?
6. **Red flags**: Check references/red-flags.md
7. **Final test**: What new fact about nature is claimed? Can you state it in one sentence?

### For Proposals

1. **Significance**: Why does this matter? Is it clearly stated upfront?
2. **Hypothesis**: Is it testable and clearly articulated?
3. **Approach**: Specific methodology? Controls? Statistical justification?
4. **Preliminary data**: Does it support feasibility of proposed work?
5. **Contingency**: Alternative approaches if primary fails?
6. **Timeline**: Realistic milestones with dates?
7. **Broader impacts** (NSF): Clearly addressed as separate section?
8. **Accessibility**: Can non-specialist reviewers follow the argument?

## Output Format

```markdown
# Scientific Writing Review

## Document Type
[Paper / Proposal / Abstract / Beamtime Request]

## Summary
[2-3 sentence assessment from reviewer perspective]

## Strengths
- [What works well - lead with positives]

## Critical Issues (address before submission)
- [ ] Issue with location/section

## Moderate Issues
- [ ] Issue with suggested fix

## Minor Polish
- [ ] Small improvements

## Red Flags Found
| Phrase | Location | Suggested Revision |
|--------|----------|-------------------|

## Questions a Reviewer Would Ask
- [Likely reviewer concerns]

## Priority Fixes
1. Most critical
2. Second priority
3. Third priority
```

## Key Principles

### Fractal Structure (Hoffman)
Your document should be understandable at multiple depths:
- **1 minute**: Abstract conveys main finding
- **5 minutes**: Figures tell the story with captions
- **10 minutes**: Intro, first sentence of each paragraph, and conclusion

### Reviewer Mindset
Reviewers are busy and may not be experts in your subfield. They will be:
- Happy if figures are clear and text flows logically
- Grumpy if they can't get main points from scanning figures and captions
- Swayed by ease of understanding regardless of scientific merit

### The Final Test
Before submission, state in 1-2 sentences:
- What is the new fact about nature you discovered?
- What do you know now that you didn't know before?

If you can't articulate this clearly, the document isn't ready.

## Reference Files

- `references/paper-checklist.md` - Scientific paper review criteria
- `references/grant-checklist.md` - Grant/proposal review criteria
- `references/style-grammar.md` - Style, clarity, grammar rules
- `references/red-flags.md` - Phrases and patterns to avoid
