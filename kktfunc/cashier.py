class Cashier():
    def __init__(self, cashier, inn):
        self.cashier = cashier
        self.inn = inn
        
    def __str__(self) -> str:
        return f'Кассир: {self.cashier}, ИНН:{self.inn}'
    
    def defaultCashier(self): #ToDO тут будет доставаться кассир по умолчанию
        pass
    