
class A: 
    def __init__(self, a): 
        # self.a = a 
        pass

    def cosas(self):
        self.a = 2



if __name__ == "__main__":
    a = A(1)
    a.cosas()
    print(a.a)
