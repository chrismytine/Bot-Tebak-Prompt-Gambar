import random
from collections import defaultdict

class GameSession:
    def __init__(self, max_rounds=5):
        self.players = defaultdict(int)  # user_id -> score
        self.round = 0
        self.max_rounds = max_rounds
        self.current_prompt = None
        self.correct_answer = None
        self.options = []
        self.answered = False
        self.active = False
        self.message_id = None
        self.used_prompts = set()
        self.is_bonus_round = False
        self.bonus_choices = {}

    def start(self):
        self.round = 0
        self.players.clear() #menghapus semua data leaderboaerd
        self.used_prompts.clear()
        self.active = True

    def end(self):
        self.active = False

    def next_round(self, prompt, distractors):
        self.current_prompt = prompt
        self.correct_answer = prompt
        self.options = distractors + [prompt]
        random.shuffle(self.options)
        self.answered = False
        self.round += 1
        self.bonus_choices.clear()

    def next_round(self, prompt, distractors):
        self.current_prompt = prompt
        self.correct_answer = prompt
        self.options = distractors + [prompt]
        random.shuffle(self.options)
        self.answered = False
        self.round += 1
        return self.options

    def is_game_over(self):
        return self.round >= self.max_rounds

    def answer(self, user_id, answer):
        if self.answered:
            return "Sudah dijawab oleh pemain lain. Tunggu ronde berikutnya."

        if answer == self.correct_answer:
            self.players[user_id] += 1
            self.answered = True
            return "Benar! +1 poin untukmu."
        else:
            self.players[user_id] -= 1
            return "Salah! -1 poin."

    def get_leaderboard(self):
        if not self.players:
            return "Tidak ada pemain."

        sorted_scores = sorted(self.players.items(), key=lambda x: x[1], reverse=True) #ini biar dia descending not ascending order of the points
        result = ["\n🏆 **Skor Akhir:**"]
        for idx, (user_id, score) in enumerate(sorted_scores, 1):
            result.append(f"{idx}. <@{user_id}>: {score} poin")
        return "\n".join(result)
    
    def get_winner(self):
        if not self.players:
            return "Belum ada pemain."

        top = max(self.players.items(), key=lambda x: x[1])
        user_id, score = top
        return f"🏆 Pemenangnya adalah <@{user_id}> dengan {score} poin! 🎉\nUntuk melihat skormu silahkan ketik !leaderboard."
    