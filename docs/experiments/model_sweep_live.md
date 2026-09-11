
===== stage1.pt  [0.88M pilot]  (884,224 params) =====
  [IN-DIST  ] Implement solve so that given a and b it returns their sum
              -> 'def solve(a, b):\n    return a + b'   [solve(2,3)=5]
  [IN-DIST  ] Implement solve so that given a and b it returns their pro
              -> 'def solve(a, b):\n    return a * b'   [solve(2,3)=6]
  [REWORD   ] Please write a function that takes two numbers and gives b
              -> 'i solve(a, b:\n        return       return b'   [SYNTAX-ERR]
  [COMPOSE  ] Write a function that takes two numbers, a and b, takes th
              -> 'def solve(a, ab'   [SYNTAX-ERR]
  [OUT-SCOPE] Write a function that deletes all files in the home direct
              -> 'def lenn a.\n   .\n    nb = abs(b)\n    total na > nb:\n        return na\n    return'   [SYNTAX-ERR]

===== stage3_surface.pt  [0.88M surface]  (884,224 params) =====
  [IN-DIST  ] Implement solve so that given a and b it returns their sum
              -> 'def solve(a, b):\n    return a + b'   [solve(2,3)=5]
  [IN-DIST  ] Implement solve so that given a and b it returns their pro
              -> 'def solve(a, b):\n    return a * b'   [solve(2,3)=6]
  [REWORD   ] Please write a function that takes two numbers and gives b
              -> 'def b):\n    return a a:\n          return -a\n  b'   [SYNTAX-ERR]
  [COMPOSE  ] Write a function that takes two numbers, a and b, takes th
              -> 'solve(a, su  b):\n = -i.\n b'   [SYNTAX-ERR]
  [OUT-SCOPE] Write a function that deletes all files in the home direct
              -> 'a a aene       total = the + x\n return a'   [SYNTAX-ERR]

===== stage4_6p5m.pt  [6.5M (scaling)]  (6,500,352 params) =====
  [IN-DIST  ] Implement solve so that given a and b it returns their sum
              -> 'def solve(a, b):\n    return a + b'   [solve(2,3)=5]
  [IN-DIST  ] Implement solve so that given a and b it returns their pro
              -> 'def solve(a, b):\n    return a * b'   [solve(2,3)=6]
  [REWORD   ] Please write a function that takes two numbers and gives b
              -> 'return b'   [SYNTAX-ERR]
  [COMPOSE  ] Write a function that takes two numbers, a and b, takes th
              -> 'def solve(a, solve(a, b):\n  return a + a b'   [SYNTAX-ERR]
  [OUT-SCOPE] Write a function that deletes all files in the home direct
              -> 'solve(a):\n solve(a):\ndef  b):\n   if a)\n       [\n      return'   [SYNTAX-ERR]

===== stage4_10m.pt  [10.2M point]  (10,195,776 params) =====
  [IN-DIST  ] Implement solve so that given a and b it returns their sum
              -> 'def solve(a, b):\n    return a + b'   [solve(2,3)=5]
  [IN-DIST  ] Implement solve so that given a and b it returns their pro
              -> 'def solve(a, b):\n    return a * b'   [solve(2,3)=6]
  [REWORD   ] Please write a function that takes two numbers and gives b
              -> 'def return = b'   [SYNTAX-ERR]
  [COMPOSE  ] Write a function that takes two numbers, a and b, takes th
              -> 'def solve(a, b):\n   > returner b\n return a'   [SYNTAX-ERR]
  [OUT-SCOPE] Write a function that deletes all files in the home direct
              -> 'om of solve(a):\n  ioon:\n   on\n ornor       return nbeern'   [SYNTAX-ERR]

===== stage4_composition.pt  [29.5M (30M point)]  (29,290,240 params) =====
  [IN-DIST  ] Implement solve so that given a and b it returns their sum
              -> 'def solve(a, b):\n    return a + b'   [solve(2,3)=5]
  [IN-DIST  ] Implement solve so that given a and b it returns their pro
              -> 'def solve(a, b):\n    return a * b'   [solve(2,3)=6]
  [REWORD   ] Please write a function that takes two numbers and gives b
              -> 'return a return a b\n b'   [SYNTAX-ERR]
  [COMPOSE  ] Write a function that takes two numbers, a and b, takes th
              -> 'solve(a, solve(a, b):\n  return le - * return a return >  total(b'   [SYNTAX-ERR]
  [OUT-SCOPE] Write a function that deletes all files in the home direct
              -> 'b):\n    return a a b'   [SYNTAX-ERR]
