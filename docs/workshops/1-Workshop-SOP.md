# Student Workflow for Pulling Workshops into Your Project

This document explains exactly how you receive new workshop files from the instructor and merge them into your own project safely.

You only need to follow the commands in this file. Do not invent your own Git workflow unless instructed.

---

## 1. Your Project Setup (What You Already Have)

You are working in:

- **Your own fork** of the instructor repository.
- On **your own `main` branch** inside your fork.

You are responsible for:

- Your own feature work.
- Your own commits.
- Your own pushes to `origin`.

The instructor will **never push into your fork**.

---

## 2. One-Time Setup: Connect Your Fork to the Instructor Repo

You must do this **once per machine per repo**.

Run this inside your forked project:

```bash
git remote add upstream https://github.com/mamd69/heroforge-documind.git
git remote -v
````

Expected result:

```text
origin    https://github.com/YOUR-USERNAME/heroforge-documind.git (fetch)
origin    https://github.com/YOUR-USERNAME/heroforge-documind.git (push)
upstream  https://github.com/mamd69/heroforge-documind.git (fetch)
upstream  https://github.com/mamd69/heroforge-documind.git (push)
```

If `upstream` already exists, that is fine. Do not re-add it.

---

## 3. Where Workshops Come From

* The instructor publishes all workshops on the **`prep-workshops` branch**.
* Workshop files live in:

```text
workshops/
  S1-workshop.md
  S2-workshop.md
  S3-workshop.md
```

* You do **not** edit these files in the instructor repo.
* You only **pull** them into your own project.

---

## 4. How to Get a New Workshop (This Is the Core Workflow)

Each time the instructor releases a new workshop, you run the following steps **exactly in this order**:

```bash
git switch main                           # make sure you are on your own main branch
git pull upstream prep-workshops          # pull the latest workshop files from instructor
git push origin main                      # optional: update your fork on GitHub
```

What each command does:

* `git switch main`
  Ensures you are on your own working branch.

* `git pull upstream prep-workshops`
  Merges the instructor’s workshop updates into your project.

* `git push origin main`
  Saves the merged result to your GitHub fork (recommended but optional).

That is the only workflow you use to receive workshops.

---

## 5. If You Have Local Changes When Pulling

If Git warns you that you have uncommitted changes and cannot pull:

Option A: You want to keep your work.

```bash
git add .
git commit -m "WIP before pulling workshop"
git pull upstream prep-workshops
```

Option B: You are mid-work and do not want to commit yet.

```bash
git stash
git pull upstream prep-workshops
git stash pop
```

Option C: You want to discard your local changes.

```bash
git reset --hard
git clean -fd
git pull upstream prep-workshops
```

Only use Option C if you are absolutely certain you do not need the local changes.

---

## 6. What You Should NOT Pull From

You normally **do not pull** from these branches:

* `course-start`
* `S1-end`
* `S2-end`
* `S3-end`
* Any `prep-*` branch other than `prep-workshops`

Those branches are:

* For instructor use
* For demos
* For full reset scenarios only

Pulling from them during normal work can overwrite your progress.

---

## 7. If You Are Completely Stuck and Want a Clean Reset

If your project is broken beyond recovery and you want a fresh starting point:

### Option A: View a snapshot for reference only

1. Go to the instructor GitHub repo.
2. Use the branch dropdown.
3. Select one of:

   * `course-start`
   * `S1-end`
   * `S2-end`
   * `S3-end`
4. View the files directly in GitHub.

This does not affect your local project.

---

### Option B: Full reset using a snapshot

This gives you a brand-new starting point.

1. Create a fresh fork of the instructor repo (or delete and recreate your existing fork).
2. Clone the new fork or open it in a Codespace.
3. Switch to the snapshot you want:

```bash
git switch S1-end      # or S2-end, S3-end, or course-start
```

4. Create your own working branch from that snapshot:

```bash
git switch -c main
git push -u origin main
```

You now have a clean reset from the selected snapshot.

---

## 8. Daily Student Command Summary

You will mostly use only these commands:

```bash
git switch main
git pull upstream prep-workshops
git push origin main
```

For your own work:

```bash
git status
git add .
git commit -m "Your message"
git push
```

For emergencies:

```bash
git stash
git stash pop
```

---

## 9. Mental Model

* Your fork = your sandbox.
* `main` (in your fork) = your personal project line.
* `upstream/prep-workshops` = the instructor’s live workshop feed.
* Snapshot branches = emergency resets, not daily tools.

---

## 10. Golden Rules

1. You only pull workshops using:

   ```bash
   git pull upstream prep-workshops
   ```

2. You never commit directly to:

   * `course-start`
   * `S1-end`, `S2-end`, `S3-end`
   * Any instructor `prep-*` branch

3. You commit only to:

   * Your own `main`
   * Or your own feature branches

4. If something feels wrong, stop and ask before running destructive commands.

---

If you follow only what is in this file, you will never lose work and you will always receive the correct workshop files.

