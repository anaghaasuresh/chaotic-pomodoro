Chaotic Pomodoro 🎯
===

## Basic Details
### Team Name: Nova

### Team Members
- Member 1: Anagha Suresh - ASIET
- Member 2: P S Sidharth - ASIET

### Project Description
A Pomodoro timer that actively works against you. You set a duration and a reason for the session — it throws false alarms, lies about how much time is left, and always gives up before the timer actually finishes.

### The Problem (that doesn't exist)
Pomodoro timers are too well-behaved. They count down exactly as promised, ring exactly on time, and never once panic you over nothing. Where's the chaos in that?

### The Solution (that nobody asked for)
A timer that fires fake "your rice is burning" / "pop quiz!" alerts mid-session depending on what you told it you're doing, then admits each one was a false alarm a couple seconds later. And no matter how long you set it for — even 30 seconds — it always quits early out of boredom instead of actually finishing, with zero shame about it.

## Technical Details
### Technologies/Components Used
For Software:
- Languages: Python, HTML, CSS, JavaScript
- Frameworks: Flask
- Libraries: Flask-CORS
- Tools: VS Code, Git, GitHub

### Implementation
For Software:

#### Installation
```
git clone <your-repo-url>
cd chaotic-pomodoro
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### Run
```
python app.py
```
Then open http://127.0.0.1:5000 in your browser.

## Project Documentation
For Software:

### Screenshots (Add at least 3)

<img width="1265" height="695" alt="image" src="https://github.com/user-attachments/assets/7e59a673-20b9-4192-90bd-880b99b3e47f" />
The main interface: a glass flip-clock timer, manual hour/minute/second controls, quick presets, and a reason field. Everything looks calm and functional here — that's the setup before the chaos starts.

<img width="1255" height="692" alt="image" src="https://github.com/user-attachments/assets/17346b8a-cbaa-4569-a4b8-596d03ee4307" />
Setting a 1-minute timer with the reason 'boiling an egg.' The backend reads free-text reasons and matches them to a category — here it correctly detected COOKING, which decides what kind of false alarms and messages this session gets.

<img width="1250" height="686" alt="image" src="https://github.com/user-attachments/assets/9cbdd67d-c245-4ac1-8dfd-12caa80e16b6" />
Mid-timer false alarm — 'Ooh, your rice has been overcooked!!' fires even though this is a 1-minute egg timer, not rice. A few seconds later it flips to an 'ooppsie, false alarm' reveal before the countdown resumes as if nothing happened.

<img width="1250" height="692" alt="image" src="https://github.com/user-attachments/assets/5dc47fd8-5dfa-4efc-b22e-fb15d129a3cc" />
The 1-minute egg timer 'completes' at 0:28 remaining — not 0:00. The app gets bored and abandons the countdown early every single time, no matter how short the duration, with a category-flavored excuse instead of an actual finish.

### Diagrams
<img width="227" height="385" alt="image" src="https://github.com/user-attachments/assets/15ff94c4-3189-4a15-b454-3e8d1deb4a95" />

## Project Demo
### Video
https://drive.google.com/file/d/1_VM0rB7J4-UsqjF-_V50yd46B4o03NMz/view?usp=sharing
This video shows a work-themed session in action. Around the 26-second mark, the timer gives up entirely and displays "I'm clocking out early. You should probably keep working though" — stopping the countdown completely instead of finishing normally. At the 30-second mark, a false alarm fires with a fake "New meeting invite: Quick Sync (2 hours)" notification, followed two seconds later by an "Ooppsie, false alarm!" reveal admitting it wasn't real. The video also demonstrates the phone-roast feature, which detects when you pick up your phone mid-session and responds with a random chaotic comment calling you out for it.

## Team Contributions
- Anagha Suresh: Backend — Flask API, timer chaos logic, false alarm scheduling
- P S Sidharth: Frontend — UI design, layout, animations, and API integration
