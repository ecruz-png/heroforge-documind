# Working with the Course Repo, Workshops, and Snapshots

### 1. How to start the course

1. Go to the instructor’s GitHub repo (your instructor will give you the link).
2. Click `Fork` to create your own copy of the repo under your account.
3. Either:

   * Create a Codespace on your fork, or
   * Clone your fork to your machine.

Your main working branch will normally be:

* `main` in **your fork**, not the instructor’s repo.

---

### 2. Recommended structure for your work

* Keep all your main project work on your `main` branch in your fork.
* When a new session S1, S2, S3 starts, you continue working in the same project rather than starting over.

---

### 3. Getting new workshop files from the instructor

Your instructor will add workshop files (for example `workshops/S1-workshop.md`, `workshops/S2-workshop.md`) to **their** `main` branch.

You need to link your fork to the instructor’s repo once, then pull updates when workshops are released.

#### 3.1 One-time setup: add `upstream` remote

In the terminal of your fork (Codespace or local):

```bash
git remote add upstream https://github.com/mamd69/heroforge-documind.git
git remote -v
```

You should now see:

* `origin` pointing to your fork
* `upstream` pointing to the instructor’s original repo

#### 3.2 Each time a new workshop is released

1. Make sure you are on your `main` branch:

   ```bash
   git switch main
   git status
   ```

2. Tell Git to merge the Instructor's changes (which should be safe as there are only new Workshop files)

    ```bash
   git config --global pull.rebase false   # tell Git "when I pull, I want merges"
   ```
    
4. Pull the latest changes from the instructor’s `main`:

   ```bash
   git pull upstream main
   ```

   This brings in new or updated workshop files like `workshops/S2-workshop.md`.

5. (Optional) Push the updated `main` back to your own fork on GitHub:

   ```bash
   git push origin main
   ```

If Git reports merge conflicts, ask for help; do not panic. Usually conflicts happen only if you edited the same files as the instructor.

---

### 4. How to use workshop files

For each session:

* Open the corresponding workshop file in your project, for example:

  * `workshops/S1-workshop.md`
  * `workshops/S2-workshop.md`
* Follow the instructions, using your existing project as the base.

You generally do not need to switch branches for workshops; you keep working on `main` in your fork unless your instructor tells you otherwise.

---

### 5. Using instructor snapshots if you get stuck

The instructor provides snapshot branches like:

* `S1-end` (end of Session 1)
* `S2-end` (end of Session 2)
* `S3-end` (end of Session 3)

These snapshots contain clean, known-good versions of the project at specific points in the course.

If you are badly stuck and want a clean starting point:

#### Option A: New fork from scratch

1. Fork the instructor’s repo again into a new GitHub repo (or delete and recreate your fork if you are comfortable doing that).

2. Clone the new fork or create a Codespace on it.

3. Switch to the snapshot branch you want:

   ```bash
   git switch S1-end      # or S2-end, S3-end
   ```

4. Start working from that snapshot.

#### Option B: Just inspect the snapshot on GitHub

If you only need to see how something is supposed to look:

1. Go to the instructor’s repo on GitHub.
2. Use the branch dropdown to select `S1-end`, `S2-end`, or `S3-end`.
3. Browse the files (and workshops) for reference.
4. Fix your own code in your fork based on what you see.

---

### 6. Summary of your day-to-day commands

Most of the time you will use:

* `git switch main`
  Make sure you are on your main working branch.

* `git pull upstream main`
  Get the instructor’s latest updates, including new workshops.

* `git status`
  Check what files you have changed and whether your working directory is clean.

* `git add .`
  Stage your changes before saving them.

* `git commit -m "Message"`
  Save a snapshot of your work.

* `git push origin main`
  Upload your changes to your fork on GitHub.

If you get stuck beyond repair, you can:

* Either ask for help with your fork, or
* Start fresh from one of the instructor’s snapshot branches (`S1-end`, `S2-end`, `S3-end`) as described above.
