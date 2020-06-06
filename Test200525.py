import sys, random

class State:
    def __init__(self, board, hand, nonp):
        self.board = board
        self.hand = hand
        self.nonp = nonp
        self.weights = 0, 2, 4, 6, 8, 10, 12, 14, 16, -16, -14, -12, -10, -8, -6, -4, -2, 0
        self.lance = [[(n, (2, 10)[n<27], n%9) for n in range(p-9, -1, -9)] for p in range(81)]
        self.major = dict((piece, [None]*81) for piece in (6, 7, 14, 15))
        self.minor = dict((piece, [None]*81) for piece in (1, 3, 4, 5, 8, 9, 10, 11, 12, 14, 15))
        ds = ((1, -1, 8), (1, 1, 10), (-1, -1, -10), (-1, 1, -8), (-1, 0, -9), (0, -1, -1), (0, 1, 1), (1, 0, 9))
        for p in range(81):
            (i, j), raid = divmod(p, 9), p<27
            self.major[ 6][p] = [[(n, (6, 14)[n<27], n%9) for n in range(p-10, p-10*(1+min(i,   j)), -10)],
                                 [(n, (6, 14)[n<27], n%9) for n in range(p- 8, p- 8*(1+min(i, 8-j)), - 8)],
                                 [(n, (6, 14)[raid], n%9) for n in range(p+10, p+10*(9-max(i,   j)),  10)],
                                 [(n, (6, 14)[raid], n%9) for n in range(p+ 8, p+ 8*(9-max(i, 8-j)),   8)]]
            self.major[ 7][p] = [[(n, (7, 15)[n<27],   j) for n in range(p-9,    -1, -9)],
                                 [(n, (7, 15)[raid],   j) for n in range(p+9,    81,  9)],
                                 [(n, (7, 15)[raid], n%9) for n in range(p-1, p-j-1, -1)],
                                 [(n, (7, 15)[raid], n%9) for n in range(p+1, p-j+9,  1)]]
            self.major[14][p] = [[(n, 14, nj) for n, _, nj in ns] for ns in self.major[6][p]]
            self.major[15][p] = [[(n, 15, nj) for n, _, nj in ns] for ns in self.major[7][p]]
            self.minor[ 1][p] = [[p-9, (1, 9)[(prom:=i<=3)], j, prom]] if i else []
            self.minor[ 3][p] = [[p+dj-18, (3, 11)[i<=4], j+dj, None] for dj in (-1, 1) if 0<=j+dj<=8] if i>=2 else []
            c = [(p+d, j+dj, 0<=i+di<=8 and 0<=j+dj<=8) for di, dj, d in ds]
            for piece, ctrl in (4,c[:5]), (5,c[2:]), (8,c), (9,c[2:]), (10,c[2:]), (11,c[2:]), (12,c[2:]), (14,c[4:]), (15,c[:4]):
                self.minor[piece][p] = [[n, piece, nj, None] for n, nj, on_board in ctrl if on_board]

    def legal_moves(self, board, hand, nonp):
        for p, p0 in enumerate(board):
            if not p0:
                for n1 in 7, 6, 5, 4:
                    if hand[n1]:
                        yield p, n1
                if p >= 18:
                    if hand[3]:
                        yield p, 3
                    if hand[2]:
                        yield p, 2
                    if nonp[p%9] and hand[1]:
                        yield p, 1
            elif p0 == 2:
                for n, n1, nj in self.lance[p]:
                    if (n0 := -board[n]):
                        if n0 > 0:
                            yield n, n1, nj, n0, p
                        break
            else:
                if p0 in self.major:
                    for ns in self.major[p0][p]:
                        for n, n1, nj in ns:
                            if (n0 := -board[n]) >= 0:
                                yield n, n1, nj, n0, p
                            if n0:
                                break
                if p0 in self.minor:
                    for n, n1, nj, pp in self.minor[p0][p]:
                        if (n0 := -board[n]) >= 0:
                            yield n, n1, nj, n0, p, pp

    def do(self, board, hand, nonp, n, n1, nj=None, n0=None, p=None, pp=None):
        board, hand, nonp = [-piece for piece in board[::-1]], hand[::-1], nonp[::-1]
        board[80-n] = -n1
        if nj == None:
            hand[-1-n1] -= 1
            if n1 == 1:
                nonp[-1-n%9] = False
        else:
            board[80-p] = 0
            if n0 >= 9:
                hand[7-n0] += 1
            elif n0:
                hand[-1-n0] += 1
                if n0 == 1:
                    nonp[8-nj] = True
            if pp:
                nonp[-1-nj] = True
        return board, hand, nonp

    def act(self, move):
        self.board, self.hand, self.nonp = self.do(self.board, self.hand, self.nonp, *move)
    
    def negamax(self, depth, alpha, beta, board, hand, nonp):
        if hand[9]:
            return -1000
        if not depth:
            return sum(board) + sum(w*p for w, p in zip(self.weights, hand))
        for move in self.legal_moves(board, hand, nonp):
            alpha = max(alpha, -self.negamax(depth-1, -beta, -alpha, *self.do(board, hand, nonp, *move)))
            if alpha >= beta:
                return alpha
        return alpha
        
    def search(self, depth=1):
        alpha, bestmove = -1000, None
        moves = list(self.legal_moves(self.board, self.hand, self.nonp))
        random.shuffle(moves)
        for move in moves:
            score = -self.negamax(depth, -1000, -alpha, *self.do(self.board, self.hand, self.nonp, *move))
            if score > alpha:
                alpha = score
                bestmove = move
        return alpha, bestmove
    
pieces, col, row = "_PLNSGBR", "987654321", "abcdefghi"

def move_to_sfen(board, turn, n, n1, nj=None, n0=None, p=None, pp=None):
    ni, nj = divmod(n, 9)
    ns = col[::turn][nj] + row[::turn][ni]
    if n0 == None:
        return pieces[n1] + "*" + ns
    pi, pj = divmod(p, 9)
    ps = col[::turn][pj] + row[::turn][pi]
    if board[p] < n1:
        return ps + ns + "+"
    return ps + ns

def sfen_to_move(board, turn, sfen):
    ni, nj = row[::turn].find(sfen[3]), col[::turn].find(sfen[2])
    n = 9 * ni + nj
    if sfen[1] == "*":
        return n, pieces.find(sfen[0])
    pi, pj = row[::turn].find(sfen[1]), col[::turn].find(sfen[0])
    p = 9 * pi + pj
    n1 = board[p]
    if sfen[-1] == "+":
        return n, n1+8, nj, -board[n], p, n1==1
    return n, n1, nj, -board[n], p

def sfen_to_state(sfen_board, sfen_hand, sfen_turn):
    pieces = {'.':0, 'P':1, 'L':2, 'N':3, 'S':4, 'G':5, 'B':6, 'R':7, 'K':8, '+P':9, '+L':10, '+N':11, '+S':12, '+B':14, '+R':15,
                     'p':-1,'l':-2,'n':-3,'s':-4,'g':-5,'b':-6,'r':-7,'k':-8,'+p':-9,'+l':-10,'+n':-11,'+s':-12,'+b':-14,'+r':-15}
    board, hand, nonp = [0]*81, [0]*18, [True]*18
    for i in range(1, 10):
        sfen_board = sfen_board.replace(str(i), "."*i)
    sfen_board = sfen_board.replace("/", "")
    for i in range(81):
        j = 1 + (sfen_board[0] == "+")
        piece = pieces[sfen_board[:j]]
        if piece == 1:
            nonp[i%9] = False
        elif piece == -1:
            nonp[-1-i%9] = False
        board[i] = piece
        sfen_board = sfen_board[j:]
    if sfen_hand != "-":
        while sfen_hand:
            if sfen_hand[0].isdigit():
                j = 1 + sfen_hand[1].isdigit()
                hand[pieces[sfen_hand[j]]] = int(sfen_hand[:j])
                sfen_hand = sfen_hand[1+j:]
            else:
                hand[pieces[sfen_hand[0]]] = 1
                sfen_hand = sfen_hand[1:]
    if sfen_turn == "b":
        return State(board, hand, nonp), 1
    return State([-piece for piece in board[::-1]], hand[::-1], nonp[::-1]), -1

DEPTH_LIMIT = 1
while True:
    cmd = input().split()
    if cmd[0] == "usi":
        print("id name Test200525")
        print("option name DepthLimit type spin default 1 min 1 max 5")
        print("usiok")
    elif cmd[0] == "isready":
        print("readyok")
    elif cmd[0] == "setoption":
        if cmd[2] == "DepthLimit":
            DEPTH_LIMIT = int(cmd[4])
    elif cmd[0] == "position":
        if cmd[1] == "startpos":
            cmd[1:2] = ["sfen", "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL", "b", "-", "1"]
        state, turn = sfen_to_state(cmd[2], cmd[4], cmd[3])
        for move in cmd[7:]:
            state.act(sfen_to_move(state.board, turn, move))
            turn *= -1
    elif cmd[0] == "go":
        score, bestmove = state.search(DEPTH_LIMIT)
        print("info score cp", 50*score)
        if score == -1000:
            print("bestmove resign")
        else:
            print("bestmove", move_to_sfen(state.board, turn, *bestmove))
    elif cmd[0] == "quit":
        sys.exit()