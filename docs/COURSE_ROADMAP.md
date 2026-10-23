# CodeLeaf Course Roadmap

This roadmap contains all 62 course tracks requested for CodeLeaf. A track is a catalog roadmap entry, not a claim that its complete lesson content, exercises, exam, or certificate has already been authored or published.

## Suggested categories

### AI & Machine Learning
- **AI Foundations** (`ai`)
- **Generative AI** (`generative-ai`)
- **PyTorch** (`pytorch`)
- **scikit-learn** (`scikit-learn`)

### Backend & APIs
- **PHP** (`php`)
- **Django** (`django`)
- **Node.js** (`nodejs`)
- **ASP** (`asp`)
- **Express.js** (`expressjs`)
- **FastAPI** (`fastapi`)
- **Flask** (`flask`)
- **REST API Development** (`rest-api-development`)

### Cloud & DevOps
- **AWS** (`aws`)
- **Git** (`git`)
- **Bash** (`bash`)
- **PowerShell** (`powershell`)
- **Docker** (`docker`)
- **Linux** (`linux`)
- **GitHub Actions** (`github-actions`)

### Computer Science
- **DSA** (`dsa`)

### Data & Analytics
- **Excel** (`excel`)
- **NumPy** (`numpy`)
- **Pandas** (`pandas`)
- **R** (`r`)
- **SciPy** (`scipy`)
- **Data Science** (`data-science`)

### Data Formats
- **XML** (`xml`)
- **JSON & YAML** (`json-yaml`)

### Databases
- **SQL** (`sql`)
- **MySQL** (`mysql`)
- **PostgreSQL** (`postgresql`)
- **MongoDB** (`mongodb`)
- **SQLite** (`sqlite`)
- **Redis** (`redis`)

### Programming
- **Python** (`python`)
- **Java** (`java`)
- **C** (`c`)
- **C++** (`cpp`)
- **C#** (`csharp`)
- **Go** (`go`)
- **Kotlin** (`kotlin`)
- **Swift** (`swift`)
- **Rust** (`rust`)
- **Dart** (`dart`)
- **Ruby** (`ruby`)
- **Lua** (`lua`)
- **Solidity** (`solidity`)

### Security
- **Cybersecurity** (`cybersecurity`)
- **Web Application Security** (`web-application-security`)

### Web Development
- **HTML** (`html`)
- **CSS** (`css`)
- **JavaScript** (`javascript`)
- **Bootstrap** (`bootstrap`)
- **React** (`react`)
- **jQuery** (`jquery`)
- **TypeScript** (`typescript`)
- **Angular** (`angular`)
- **AngularJS** (`angularjs`)
- **Sass** (`sass`)
- **Vue.js** (`vue`)
- **Next.js** (`nextjs`)
- **Tailwind CSS** (`tailwind-css`)

## Curriculum production status

- Each track starts as **Roadmap** and has zero published lessons in the catalog until the reviewed manifest is imported.
- Use `docs/MASTER_COURSE_PROMPT.md` separately for each track.
- Generate the complete syllabus and stable lesson IDs first, review it, then generate detailed lessons in batches.
- Include visuals, runnable examples where the technology supports them, practice, solutions, projects, assessments and QA.
- Do not publish the exam/certificate as a real credential until the question bank, grading, pass rules, certificate ID and verification endpoint are implemented and reviewed.
- Only run user code in a separately isolated runner; never execute submitted snippets inside the FastAPI process.

## Priority deployment sequence

1. Publish the shell and approved initial curricula.
2. Deploy the static React/Vite frontend to Vercel.
3. Deploy the FastAPI backend to Render.
4. Use managed PostgreSQL on Neon, keeping credentials server-side.
5. Add a separately isolated code-runner service before enabling arbitrary code execution.
6. Add object storage for project uploads/assets and monitoring/backups before broad public launch.
