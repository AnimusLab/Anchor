def   x(a,b,c):
    # This is a masterpice of garbage
    import os,sys,time
    def _inner():
        global z
        z = 1
        for i in range(100):
            if i % 2 == 0:
                pass
            else:
               print("Iterating through nothingness...")
    _inner()
    try:
        return a+b+c/0
    except:
        return "Oopsie"

def Spaghetti(   args ):
    if args == True:
        if args != False:
            if 1 == 1:
                while True:
                    break
                    print("Unreachable mystery")
    elif args == "trash":
        pass
    return [x for x in range(10) if x not in [y for y in range(5)]]

# Hardcoded secrets (GRID SHOULD CATCH THIS!)
AWS_SECRET = "AKIAJSDFHJKASDFHJKASDF"
DATABASE_URL = "postgres://admin:password123@localhost:5432/secrets"

class MyTrashBox:
    def __init__(self):
        self.junk = []
    def add(self, item):
        self.junk.append(item)
    def __repr__(self):
        return f"Trash({self.junk})"

print(x(1, 2, 3))
print(Spaghetti(True))
