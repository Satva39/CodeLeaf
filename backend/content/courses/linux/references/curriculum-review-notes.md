# Curriculum coverage and review notes

- Source: supplied `Linux.pdf` (58 pages); source text extracted and the numbered Section B lesson headings compared against the parsed curriculum.
- Review date: 2026-10-20.
- Scope: exactly the Linux course; no other course folders or application code were modified.
- Publication: draft; the generated content and knowledge checks require human technical review before publication.

## Numbered syllabus coverage

| Module | Title | Lessons | Lesson range |
|---:|---|---:|---:|
| 1 | Introduction to Linux | 8 | 1–8 |
| 2 | Linux Installation and Environment Setup | 8 | 9–16 |
| 3 | The Linux Terminal and Command-Line Fundamentals | 10 | 17–26 |
| 4 | Linux Filesystem and Directory Navigation | 8 | 27–34 |
| 5 | File Operations and Text Processing | 11 | 35–45 |
| 6 | Editors, Documentation, and Everyday Tools | 5 | 46–50 |
| 7 | Users, Groups, Permissions, and Ownership | 9 | 51–59 |
| 8 | Package Management and Software Installation | 9 | 60–68 |
| 9 | Processes, Jobs, and Resource Management | 9 | 69–77 |
| 10 | Boot Process, Init Systems, and Services | 10 | 78–87 |
| 11 | Disks, Filesystems, and Storage Management | 12 | 88–99 |
| 12 | Linux Networking Fundamentals | 12 | 100–111 |
| 13 | Remote Access and File Transfer | 9 | 112–120 |
| 14 | Bash and Shell Fundamentals | 13 | 121–133 |
| 15 | Shell Scripting and Automation | 10 | 134–143 |
| 16 | Scheduling, Logs, and Monitoring | 10 | 144–153 |
| 17 | Linux Server Administration | 11 | 154–164 |
| 18 | Linux Security and System Hardening | 13 | 165–177 |
| 19 | Troubleshooting, Recovery, and Diagnostics | 11 | 178–188 |
| 20 | Linux Kernel, Hardware, and System Internals | 11 | 189–199 |
| 21 | Performance and Capacity Optimization | 10 | 200–209 |
| 22 | Developer Workflows on Linux | 8 | 210–217 |
| 23 | Virtualization, Containers, and Isolation | 10 | 218–227 |
| 24 | Production Operations, Cloud, and Reliability | 10 | 228–237 |
| 25 | Linux Desktop and End-User Administration | 7 | 238–244 |
| 26 | Embedded Linux, Specialized Systems, and Legacy Environments | 8 | 245–252 |
| 27 | Professional Linux Practices and Career Preparation | 5 | 253–257 |

All 257 numbered headings from Section B are represented in individual lesson JSON files. The ordered subtopic lines from the PDF are stored in each corresponding lesson. The module names and lesson titles follow the source syllabus; wrapped module title 26 is reconstructed as “Embedded Linux, Specialized Systems, and Legacy Environments.”

## Practical sections

- **Section C:** the 12 beginner (B01–B12), 12 intermediate (I01–I12), and 10 advanced (A01–A10) exercises are separate files attached to relevant lessons. In addition, each of the 257 numbered lessons has its own linked practice task. All are draft and emphasize repeatable evidence in a safe lab.
- **Section D:** the 12 projects (four beginner, four intermediate, and four advanced) plus the “Production-Ready Linux Server Platform” capstone have independent project files, starter files, rubrics totaling 100 points, and protected reference outlines.
- **Section E:** core professional topics, six specialist tracks, and optional ecosystem tools are recorded in `references/specialist-tracks.json`.
- **Section F:** six learning phases, checkpoints, suggested learner paths, and a prerequisite map are in `references/learning-roadmap.md`.
- **Section G:** coverage is retained by mapping the Section B topics into these modules; source-recommended technical accuracy and safety requirements are incorporated below.

## Corrections, scope notes, and safe interpretation

1. **Kernel versus operating system:** the PDF correctly states that Linux is technically the kernel. Course explanations preserve the distinction between kernel, userspace, and a distribution; “Linux OS” is used conversationally only where the context is clear.
2. **Distribution-specific behavior:** APT, DNF/RPM, pacman, zypper, apk, NetworkManager, Netplan, systemd, OpenRC, nftables, firewalld, UFW, and security policy are not interchangeable. Lessons label or call out variation instead of claiming a single command works on every distribution.
3. **Modern versus legacy tooling:** `ip` and `ss` are taught for modern network inspection; historical tools such as `ifconfig` and `netstat` remain appropriate in the legacy lesson, with availability caveats. No topic is silently dropped for being older.
4. **Containers versus virtual machines:** container content states that conventional Linux containers share the host kernel, whereas VMs virtualize a machine boundary. The security explanation does not claim either isolation model is perfect.
5. **Potentially destructive operations:** installation, partitioning/formatting, filesystem repair, permission recursion, account changes, firewall rules, boot configuration, package removal, and service changes must be practised in a disposable VM or explicitly authorized lab with a backup and rollback plan. The lesson snippets prioritize read-only/print-only examples.
6. **Code execution:** CodeLeaf has no isolated Linux/Bash runner in this ZIP. Shell examples are therefore marked `manual-terminal`; no backend endpoint or production process executes learner shell commands. A separate sandboxed runner would require its own threat model, limits, filesystem/network policy, and deployment.
7. **Assessments:** question answer keys and explanations are stored under the existing protected question-file convention. All content remains draft; answer keys and distractors should be reviewed before any publish import.
8. **Generated content review:** lesson-specific explanations, safe examples, SVGs, practice prompts, and assessment drafts are newly authored for this patch. Official reference links anchor technical follow-up; they do not mean every command was executed on every listed distribution.

## Visual pages and source references

The PDF includes small embedded image assets and terminal/diagram imagery in its later practical section (notably pages 48–50 in the extracted image inventory). This patch does not copy those images; it supplies original SVG roadmaps and concept diagrams with alt text and captions. Source pages remain the authority for the curriculum outline.

## Validation limits

Filesystem/JSON/schema validation can prove file paths, IDs, lesson links, asset XML, and counts are consistent. It cannot prove live PostgreSQL import, learner API behavior, command execution across distributions, or the production deployment unless those systems are actually run and reviewed. Keep this course in draft until review and isolated lab checks are complete.
