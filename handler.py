from structures import Variable, Iter, Array
import sys

class Handler:
    global line_counter
    
    def __init__(self, bison_task, symbol_table):
        self.bison_task = bison_task
        self.symbol_table = symbol_table
        self.code = []
        self.iterators = []
        self.code.append("RESET g")
        self.code.append("INC g")
        self.code.append("RESET h")
        self.code.append("DEC h")

    def start(self):
        self.read_bison(self.bison_task)
        self.code.append("HALT")
        return self.code

    def write(self, tag, variable):
        # Write 2;
        if tag == "num":
            self.get_num(variable, 'a')
        # Write a;
        elif tag == "LOAD":
            if type(variable) == tuple:
                # to jest array
                if variable[0] == "array":
                    self.load_arr(variable[1], variable[2], 'a', 'b')
                elif variable[0] == 'undeclared':
                    raise Exception(f"Unknown variable {variable[1]}")
            else:
                self.load_var(variable, 'a')

        self.code.append(f"PUT")

    def read(self, variable):
        # to jest array
        if type(variable) == tuple:
            # to jest array
            if variable[0] == "array":
                self.load_arr_pointer(variable[1], variable[2], 'b', 'c')
            elif variable[0] == 'undeclared':
                raise Exception(f"Unknown variable {variable[1]}")
        # to jest pojedyczna zmienna
        else:
            self.symbol_table[variable].initialized = True
            self.load_var_pointer(variable, 'b')
            
        
        self.code.append(f"GET")
        self.code.append(f"STORE b")

    def assign(self, variable, expression):  
        self.solve(expression)
        # to jest array

        if type(variable) == tuple:
            # to jest array
            if variable[0] == "array":
                self.load_arr_pointer(variable[1], variable[2], 'b', 'c')     
            elif variable[0] == 'undeclared':
                raise Exception(f"STH WRONG, SHOULD NEVER raised")
        # to jest pojedyczna zmienna
        else:
            if type(self.symbol_table[variable]) == Variable:
                self.symbol_table[variable].initialized = True
                self.load_var_pointer(variable, 'b')
            else: 
                raise Exception(f"Try assign array as variable")
                
                

        self.code.append(f"STORE b")
        
    def ifelse(self, conditionn, expression_1, expression_2): 
        condition_result = self.num_condition(conditionn)
        if isinstance(condition_result, bool):
            if condition_result:
                self.read_bison(expression_1)
            else:
                self.read_bison(expression_2)
        else:
            condition_start = len(self.code)
            self.solve_condition(conditionn)
            if_start = len(self.code)
            self.read_bison(expression_1)
            self.code.append(f"JUMP over_else_mark")
            else_start = len(self.code)
            self.read_bison(expression_2)
            command_end = len(self.code)
            self.code[else_start - 1] = self.code[else_start - 1].replace('over_else_mark',
                                                                          str(command_end - else_start + 1))
            for i in range(condition_start, if_start):
                self.code[i] = self.code[i].replace('if_mark', str(else_start - i))
        
    def iff(self, condition, expression):
        condition_result = self.num_condition(condition)
        if isinstance(condition_result, bool):
            if condition_result:
                self.read_bison(expression)
        else:
            condition_start = len(self.code)
            self.solve_condition(condition)
            command_start = len(self.code)
            self.read_bison(expression)
            command_end = len(self.code)
            for i in range(condition_start, command_start):
                self.code[i] = self.code[i].replace('if_mark', str(command_end - i))    
                
    def whilee(self, condition, expression):
        condition_result = self.num_condition(condition)
        if isinstance(condition_result, bool):
            if condition_result:
                loop_start = len(self.code)
                self.read_bison(expression)
                self.code.append(f"JUMP {loop_start - len(self.code)}")
        else:
            condition_start = len(self.code)
            self.solve_condition(condition)
            loop_start = len(self.code)
            self.read_bison(expression)
            self.code.append(f"JUMP {condition_start - len(self.code)}")
            loop_end = len(self.code)
            for i in range(condition_start, loop_start):
                self.code[i] = self.code[i].replace('if_mark', str(loop_end - i))
                
    def repeat(self, condition, expression):
        loop_start = len(self.code)
        self.read_bison(expression)
        condition_start = len(self.code)
        condition_result = self.num_condition(condition)
        if isinstance(condition_result, bool):
            pass
        else:
            self.solve_condition(condition)
        condition_end = len(self.code)
        for i in range(condition_start, condition_end):
            self.code[i] = self.code[i].replace('if_mark', str(loop_start - i))
            
                
    def forto(self, iterator, low, high, expression):
        if low[0] == high[0] == "const":
            if low[1] > high[1]:
                return

        if self.iterators:
            address_val, limit_address = self.symbol_table.get_iter(self.iterators[-1])
            self.get_num(address_val, 'a')
            self.code.append(f"SWAP f")
            self.code.append(f"STORE f")
            

        self.symbol_table.add_iter(iterator)
        
        address_val, addres_limit = self.symbol_table.get_iter(iterator)
        self.solve(low)
        
        self.code.append("SWAP f")
        self.iterators.append(iterator)
        self.solve(high)
        self.code.append(f"INC a")
        
        self.get_num(addres_limit, 'b')
        self.code.append(f"STORE b")

        self.code.append(f"SWAP e")
        

        condition_start = len(self.code)
        self.code.append("RESET a")
        self.code.append("ADD e")

        self.code.append("SUB f")
        
        self.code.append("JNEG finish")

        loop_start = len(self.code)
        
        self.read_bison(expression)
        
        self.code.append("INC f")
        
        self.get_num(addres_limit, 'b')
        self.code.append(f"LOAD b")
        self.code.append(f"SWAP e")
        
        self.code.append(f"JUMP {condition_start - len(self.code)}")
        loop_end = len(self.code)

        self.code[loop_start - 1] = f"JZERO {loop_end - loop_start + 1}"

        self.iterators.pop()
        self.symbol_table.iterators.pop(iterator)
        
        if self.iterators:
            address_val, limit_address = self.symbol_table.get_iter(self.iterators[-1])
            self.get_num(address_val, 'a')
            self.code.append(f"LOAD a")
            self.code.append(f"SWAP f")
            
    def fordown(self, iterator, low, high, expression):
        if low[0] == high[0] == "const":
            if low[1] < high[1]:
                return

        if self.iterators:
            address_val, limit_address = self.symbol_table.get_iter(self.iterators[-1])
            self.get_num(address_val, 'a')
            self.code.append(f"SWAP f")
            self.code.append(f"STORE f")
            

        self.symbol_table.add_iter(iterator)
        
        address_val, addres_limit = self.symbol_table.get_iter(iterator)
        self.solve(low)
        self.code.append("SWAP f")
        
        
        self.solve(high)
        self.code.append(f"DEC a")
        
        self.get_num(addres_limit, 'b')
        self.code.append(f"STORE b")
        self.code.append(f"SWAP e")
        self.iterators.append(iterator)
        
        condition_start = len(self.code)
        self.code.append("RESET a")
        self.code.append("SUB e")
        self.code.append("ADD f")
        
        
        self.code.append("JNEG finish")

        loop_start = len(self.code)
        
        self.read_bison(expression)
        
        self.code.append("DEC f")
        
        self.get_num(addres_limit, 'b')
        self.code.append(f"LOAD b")
        self.code.append(f"SWAP e")
        
        self.code.append(f"JUMP {condition_start - len(self.code)}")
        loop_end = len(self.code)

        self.code[loop_start - 1] = f"JZERO {loop_end - loop_start + 1}"

        self.iterators.pop()
        self.symbol_table.iterators.pop(iterator)
        
        if self.iterators:
            address_val, limit_address = self.symbol_table.get_iter(self.iterators[-1])
            self.get_num(address_val, 'a')
            self.code.append(f"LOAD a")
            self.code.append(f"SWAP f")
            
            
    def read_bison(self, bison_task):
        for task in bison_task:
            print(task)
            self.symbol_table.line_counter = task[1]
            task = task[0]
            
            if task[0] == "WRITE":
                self.write(task[1][0], task[1][1])
            elif task[0] == "READ":
                self.read(task[1])
            elif task[0] == "ASSIGN":
                self.assign(task[1], task[2])      
            elif task[0] == "IF":
                self.iff(task[1], task[2])
            elif task[0] == "IFELSE":
                self.ifelse(task[1], task[2], task[3])
            elif task[0] == "WHILE":
                self.whilee(task[1], task[2])
            elif task[0] == "REPEAT":
                self.repeat(task[1], task[2])
            elif task[0] == "FORTO":
                self.forto(task[1], task[2], task[3], task[4])
            elif task[0] == "FORDOWN":
                self.fordown(task[1], task[2], task[3], task[4])


    # pod zadanym adresem zadana liczba
    def get_num(self, num, register_1):
        self.code.append(f"RESET {register_1}")
        self.code.append(f"SWAP {register_1}")
        
        minus = 0 

        if num > 0:
            bits = bin(num)[2:]
            minus = 0 
        elif num < 0:
            minus = 1
            bits = bin(-num)[2:]
        else:
            self.code.append(f"SWAP {register_1}")
            return
        
        for bit in bits[:-1]:
            if bit == '1':
                if minus:
                    self.code.append(f"DEC a")
                else:
                    self.code.append(f"INC a")
            self.code.append(f"SHIFT g")
            
        if bits[-1] == '1':
            if minus:
                self.code.append(f"DEC a")
            else:
                self.code.append(f"INC a")
        
        self.code.append(f"SWAP {register_1}")

    # pod register_1 rozwiazanie
    def solve(self, expression, register_1='a', register_2='b', register_3='c', register_4='d', register_5='e'):

        if expression[0] == "num":
            self.get_num(expression[1], register_1)
        elif expression[0] == "LOAD":
            
            if type(expression[1]) == tuple:
                # to jest array
                if expression[1][0] == "array":
                    self.load_arr(expression[1][1], expression[1][2], register_1, register_2)
                elif expression[1][0] == 'undeclared':
                    raise Exception(f"Unknown variable {expression[1][1]}")
            # to jest pojedyczna zmienna
            else:
                self.load_var(expression[1], register_1)
 

        else:
            if expression[1][0] == 'num':
                num, var = 1, 2
            elif expression[2][0] == 'num':
                num, var = 2, 1
            else:
                num = None

            if expression[0] == "PLUS":
                if expression[1][0] == expression[2][0] == "num":
                    self.get_num(expression[1][1] + expression[2][1], register_1)

                elif expression[1] == expression[2]:
                    self.solve(expression[1], register_1, register_2)
                    if register_1 == 'a':
                        self.code.append(f"SHIFT g")
                    else:
                        raise Exception(f"IMPOSIBBLE")
                else:
                    self.solve(expression[1], register_1, register_2)
                    self.solve(expression[2], register_2, register_3)
                    if register_1 != 'a':
                        raise Exception(f"IMPOSIBBLE")
                    self.code.append(f"ADD {register_2}")

            elif expression[0] == "MINUS":
                if expression[1][0] == expression[2][0] == "num":
                    self.get_num(expression[1][1] - expression[2][1], register_1)
                elif expression[1] == expression[2]:
                    self.check_init(expression[1])
                    self.check_init(expression[2])
                    self.code.append(f"RESET {register_1}")
                else:
                    self.solve(expression[1], register_1, register_2)
                    self.solve(expression[2], register_2, register_3)
                    if register_1 != 'a':
                        raise Exception(f"IMPOSIBBLE")
                    self.code.append(f"SUB {register_2}")

            elif expression[0] == "TIMES":
                if expression[1][0] == expression[2][0] == "num":
                    self.get_num(expression[1][1] * expression[2][1], register_1)
                    return

                if num:
                    val = expression[num][1]
                    # mnozenie przez zero daje 0
                    if val == 0:
                        self.check_init(expression[var])
                        self.code.append(f"RESET {register_1}")
                        return
                    # mnozenie przez jeden daje ta sama liczbe
                    elif val == 1:
                        self.solve(expression[var], register_1, register_2)
                        return
                    elif val == -1:
                        self.solve(expression[var], register_1, register_2)
                        if register_1 == 'a':
                            self.code.append(f"RESET {register_2}")
                            self.code.append(f"SWAP {register_2}")
                            self.code.append(f"SUB {register_2}")
                        else:
                            raise Exception(f"IMPOSIBBLE")
                        return
                    elif val & (val - 1) == 0:
                        self.solve(expression[var], register_1, register_2)
                        if register_1 == 'a':
                            while val > 1:
                                self.code.append(f"SHIFT g")
                                val /= 2
                            return
                        else:
                            raise Exception(f"IMPOSIBBLE")
                    elif val < 0 and -val & (-val - 1) == 0:
                        val *= -1
                        self.solve(expression[var], register_1, register_2)
                        if register_1 == 'a':
                            while val > 1:
                                self.code.append(f"SHIFT g")
                                val /= 2
                            self.code.append(f"RESET {register_2}")
                            self.code.append(f"SWAP {register_2}")
                            self.code.append(f"SUB {register_2}")
                        else:
                            raise Exception(f"IMPOSIBBLE")
                        return

                if expression[1] == expression[2]:
                    self.solve(expression[1], register_1, register_3)
                    self.code.append(f"RESET {register_3}")
                    self.code.append(f"SWAP {register_3}")
                    self.code.append(f"ADD {register_3}")
                    self.code.append(f"SWAP {register_2}")
                    if register_1 != 'a':
                        raise Exception(f"IMPOSIBBLE")
                else:
                    self.solve(expression[1], register_1, register_2)
                    self.code.append(f"SWAP {register_2}")
                    self.solve(expression[2], register_1, register_3)
                    self.code.append(f"SWAP {register_3}")

                self.multiply_code(register_1, register_2, register_3, register_4, register_5)
            elif expression[0] == "DIV":
                if register_1 != 'a':
                        raise Exception(f"IMPOSIBBLE")
                if expression[1][0] == expression[2][0] == "num":
                    

                    if expression[2][1] != 0:
                        self.get_num(expression[1][1] // expression[2][1], register_1)
                    else:
                        self.code.append(f"RESET {register_1}")
                    return

                elif expression[1] == expression[2]:
                    self.solve(expression[1], register_1, register_2)
                    self.code.append(f"JZERO 3")
                    self.code.append(f"RESET {register_1}")
                    self.code.append(f"INC {register_1}")
                    return

                elif num and num == 1 and expression[num][1] == 0:
                    self.check_init(expression[2])
                    self.code.append(f"RESET {register_1}")
                    return

                elif num and num == 2:
                    self.check_init(expression[1])
                    val = expression[num][1]
                    if val == 0:
                        self.code.append(f"RESET {register_1}")
                        return
                    elif val == 1:
                        self.solve(expression[var], register_1, register_2)
                        return
                    elif val & (val - 1) == 0:
                        self.solve(expression[var], register_1, register_2)
                        while val > 1:
                            self.code.append(f"SHIFT h")
                            val /= 2
                        return
                    elif val < 0  and -val & (-val - 1) == 0:
                        val *= -1
                        self.solve(expression[var], register_1, register_2)
                        while val > 1:
                            self.code.append(f"SHIFT h")
                            val /= 2
                        self.code.append(f"RESET {register_2}")
                        self.code.append(f"SWAP {register_2}")
                        self.code.append(f"SUB {register_2}")
                        return
                        
                self.solve(expression[1], register_1, register_2)
                self.code.append(f"SWAP {register_3}")
                self.solve(expression[2], register_1, register_2)
                self.code.append(f"SWAP {register_4}")
                self.divide_code(register_1, register_2, register_3, register_4, register_5)
            elif expression[0] == "MOD":
                if expression[2][0] == "num" and (expression[2][1] == 0 or expression[2][1] == 1 or expression[2][1] == -1):
                    self.check_init(expression[1])
                    self.code.append(f"RESET {register_1}")
                    return
                elif expression[1] == expression[2]:
                    self.check_init(expression[1])
                    self.check_init(expression[2])
                    self.code.append(f"RESET {register_1}")
                    return
                elif expression[1][0] == expression[2][0] == "num":
                    self.get_num(expression[1][1] % expression[2][1], register_1)
                    return
                elif num and num == 1 and expression[num][1] == 0:
                    self.check_init(expression[2])
                    self.code.append(f"RESET {register_1}")
                    return

                elif num and num == 2:
                    val = expression[num][1]
                    self.check_init(expression[1])
                    if val == 2:
                        self.solve(expression[var], register_1, register_2)
                        self.code.append(f"RESET {register_2}")
                        self.code.append(f"JNEG 2")     # NEGATIVE x
                        self.code.append(f"JUMP 4")    # POSTIVIVE x
                        self.code.append(f"SWAP {register_2}")
                        self.code.append(f"SUB {register_2}")
                        self.code.append(f"RESET {register_2}")
                        
                        self.code.append(f"SWAP {register_2}")
                        self.code.append(f"ADD {register_2}")
                        self.code.append(f"SHIFT h")
                        self.code.append(f"SHIFT g")
                        self.code.append(f"SUB {register_2}")
                        self.code.append(f"JZERO 3")      # koniec
                        self.code.append(f"RESET {register_1}")
                        self.code.append(f"INC {register_1}")
                        
                        # koniec
                        return
                    elif val == -2:
                        self.solve(expression[var], register_1, register_2)
                        self.code.append(f"RESET {register_2}")
                        self.code.append(f"JNEG 2")     # NEGATIVE x
                        self.code.append(f"JUMP 4")    # POSTIVIVE x
                        self.code.append(f"SWAP {register_2}")
                        self.code.append(f"SUB {register_2}")
                        self.code.append(f"RESET {register_2}")

                        self.code.append(f"SWAP {register_2}")
                        self.code.append(f"ADD {register_2}")
                        self.code.append(f"SHIFT h")
                        self.code.append(f"SHIFT g")
                        self.code.append(f"SUB {register_2}")
                        self.code.append(f"JZERO 3")      # koniec
                        self.code.append(f"RESET {register_1}")
                        self.code.append(f"DEC {register_1}")
                        
                        # koniec
                        return
                    
                self.solve(expression[1], register_1, register_2)
                self.code.append(f"SWAP {register_3}")
                self.solve(expression[2], register_1, register_2)
                
                self.code.append(f"SWAP {register_4}")
                self.divide_code(register_1, register_2, register_3, register_4, register_5)
                self.code.append(f"SWAP {register_2}")
                


    def check_init(self, identifier):
        if identifier[0] == 'undeclared':
            raise Exception(f"Unknown variable {identifier[1]}")
        elif type(identifier[1]) == tuple:
            if identifier[1][0] == 'undeclared':
                raise Exception(f"Unknown variable {identifier[1][1]}")
        elif identifier[0] == 'LOAD':
            if type(identifier[1]) == tuple:
                if identifier[1][0] == "array":
                    idx = identifier[1][2]
                    if type(idx) == tuple:
                        if idx[0] == 'undeclared':
                            raise Exception(f"SHOULD NEVER RAISED")
                elif identifier[1][0] == 'undeclared':
                    raise Exception(f"Unknown variable {identifier[1][1]}")
            # to jest pojedyczna zmienna
            else:
                if identifier[1] in self.iterators or (type(self.symbol_table[identifier[1]]) == Variable and self.symbol_table[identifier[1]].initialized):
                    pass
                else:
                    raise Exception(f"Unknown variable {identifier[1]}")
            
        

    def divide_code(self, quotient_register='a', remainder_register='b', dividend_register='c', divisor_register='d', temp_register='e'):
        start = len(self.code)
        
        
        
        self.code.append(f"SWAP {dividend_register}")
        self.code.append(f"JPOS check")  # check
        self.code.append(f"SWAP {dividend_register}")
        self.code.append(f"RESET {quotient_register}")
        self.code.append(f"SUB {dividend_register}")
        self.code.append(f"SWAP {dividend_register}")
        self.code.append(f"SWAP {divisor_register}")
        self.code.append(f"JPOS minus")  # minus
        self.code.append(f"SWAP {divisor_register}")
        self.code.append(f"RESET {quotient_register}")
        self.code.append(f"SUB {divisor_register}")
        self.code.append(f"SWAP {divisor_register}")
        ################################## -1
        self.code.append(f"INC h")  
        self.code.append(f"JUMP correct") # start
        

        minus = len(self.code)
        ############################# -2
        self.code.append(f"DEC h")
        self.code.append(f"SWAP {divisor_register}")
        self.code.append(f"JUMP correct") # start
        
        minus_change = len(self.code)
        ####################### 0
        self.code.append(f"SWAP {divisor_register}")
        self.code.append(f"RESET {quotient_register}")
        self.code.append(f"SUB {divisor_register}")
        self.code.append(f"SWAP {divisor_register}")
        self.code.append(f"JUMP correct")  # start
        
        check = len(self.code)
        self.code.append(f"SWAP {dividend_register}")
        self.code.append(f"SWAP {divisor_register}")
        self.code.append(f"JNEG -7")  # minus_change
        self.code.append(f"SWAP {divisor_register}")
        self.code.append(f"INC h")
        self.code.append(f"INC h")
        ############################################# # 1
        # start
        correct = len(self.code)
        # init i sprawdzenie czy nie zwrocic 0
        self.code.append(f"RESET {quotient_register}")
        self.code.append(f"RESET {remainder_register}")
        self.code.append(f"SWAP {divisor_register}")
        
        
        self.code.append(f"JZERO end_div")   #need swap divisor
        # ustawienei x-y, x, y, y, ~
        self.code.append(f"SWAP {dividend_register}")
        self.code.append(f"SWAP {remainder_register}")
        self.code.append(f"RESET {quotient_register}")
        self.code.append(f"ADD {dividend_register}")
        self.code.append(f"SWAP {divisor_register}")
        self.code.append(f"ADD {remainder_register}")
        self.code.append(f"SUB {dividend_register}")
        
        
        
        # a/b
        # sprawia, żę b jest jest tego samego rzedu co a
        self.code.append(f"JZERO end_div_INC_REM") # jeśli x = y   
        self.code.append(f"JNEG end_div_ZERO_REM") # jeśli x < y   a = x - y, rem = x
        self.code.append(f"RESET {quotient_register}")
        self.code.append(f"JUMP 5")   #zwieksz od razu y (shift g) ##########################3
        
        self.code.append(f"RESET {quotient_register}")
        self.code.append(f"ADD {dividend_register}")
        self.code.append(f"SUB {remainder_register}")
        self.code.append(f"JPOS 7") # shift h #####################################################

        
        self.code.append(f"SWAP {dividend_register}")
        self.code.append(f"RESET g")
        self.code.append(f"INC g")
        self.code.append(f"SHIFT g")
        self.code.append(f"SWAP {dividend_register}")
        self.code.append(f"JUMP -9") # do reset quoteint ################################################

        self.code.append(f"SWAP {dividend_register}")
        self.code.append(f"RESET g")
        self.code.append(f"DEC g")
        self.code.append(f"SHIFT g")
        self.code.append(f"SWAP {dividend_register}")
        

        
        # mamy tutaj (y`-x, x, y`, y, ~)   start
        block_PRE = len(self.code)
        self.code.append(f"RESET {quotient_register}")
        
        self.code.append(f"ADD {dividend_register}")
        self.code.append(f"SUB {remainder_register}")
        # jesli a < zwiekszone b to zakoncz else dodaj quotient
        self.code.append(f"JPOS end_div_ZERO")        # KONIEC/RESET/INC ???????
        
        
        #optymalniejszy block_FTL na pierwszy raz
        self.code.append(f"RESET {quotient_register}")
        self.code.append(f"SWAP {remainder_register}")

        
        self.code.append(f"SUB {dividend_register}")
        self.code.append(f"SWAP {remainder_register}")
        self.code.append(f"RESET {quotient_register}")
        self.code.append(f"INC {quotient_register}")
        self.code.append(f"JUMP midblock_start")
        
        block_FTL = len(self.code)  # quot in tmp
        self.code.append(f"RESET {quotient_register}")
        self.code.append(f"ADD {dividend_register}")
        self.code.append(f"SUB {remainder_register}")
        self.code.append(f"JPOS end_div_TMP")
        self.code.append(f"RESET {quotient_register}")  # quotient jest w tmp
        self.code.append(f"SWAP {remainder_register}")
        self.code.append(f"SUB {dividend_register}")
        self.code.append(f"SWAP {remainder_register}")
        self.code.append(f"SWAP {temp_register}")
        self.code.append(f"INC {quotient_register}")

        midblock_start = len(self.code)
        self.code.append(f"RESET {temp_register}")
        self.code.append(f"SWAP {temp_register}")
        self.code.append(f"ADD {dividend_register}")
        self.code.append(f"SUB {remainder_register}")
        # jesli to sprobuj zmiescic tyle razy ile mozesz wpp zmniejsz dzielnik 
        self.code.append(f"JZERO block_FTL")   # quot in temp
        self.code.append(f"JNEG block_FTL") # quot in temp
        
        

        
        self.code.append(f"SWAP {dividend_register}")
        self.code.append(f"RESET g")
        self.code.append(f"DEC g")
        self.code.append(f"SHIFT g")
        self.code.append(f"SWAP {dividend_register}")
        
        
        
        
        self.code.append(f"RESET {quotient_register}")  #quot in tmp

        self.code.append(f"ADD {divisor_register}")
        self.code.append(f"SUB {dividend_register}")
        # jesli a < zwiekszone b to zakoncz else dodaj quotient
        
        self.code.append(f"JPOS end_div_TMP") # quot in tmp

        self.code.append(f"SWAP {temp_register}")

        self.code.append(f"RESET g")
        self.code.append(f"INC g")
        self.code.append(f"SHIFT g")
        
        self.code.append(f"JUMP midblock_start")

        end_div_ZERO_REM = len(self.code)   # jeśli x < y   a = x - y, rem = x => a=0, rem = x
        self.code.append(f"RESET {quotient_register}") #ABY WYZEROWAC
        self.code.append(f"JUMP 9")
        end_div_INC_REM = len(self.code)  # a = 0, rem = x  => a=1, b = 0
        self.code.append(f"INC {quotient_register}")
        self.code.append(f"RESET {remainder_register}")
        self.code.append(f"JUMP 6")
        end_div_ZERO = len(self.code)
        self.code.append(f"RESET {quotient_register}") #ABY WYZEROWAC
        self.code.append(f"JUMP 4")
        end_div_INC = len(self.code)
        self.code.append(f"INC {quotient_register}")
        self.code.append(f"JUMP 2")
        end_div_TMP = len(self.code)
        self.code.append(f"SWAP {temp_register}")
        end_div = len(self.code)
        
        end = len(self.code)
    

        
    
        # sprawdzeni czy trzebe quo = -quo - 1
        self.code.append(f"SWAP h")
        self.code.append(f"JNEG 3")
        self.code.append(f"SWAP h")# H UJEMNY
        self.code.append(f"JUMP 6")
        self.code.append(f"SWAP h")
        self.code.append(f"RESET {temp_register}")
        self.code.append(f"SWAP {temp_register}")
        self.code.append(f"SUB {temp_register}")
        self.code.append(f"DEC {quotient_register}")
        

        
        # sprawdzeni czy trzebe rem = div - rem
        self.code.append(f"SWAP h")
        self.code.append(f"JNEG 3")
        self.code.append(f"SWAP h")
        self.code.append(f"JUMP 7")
        self.code.append(f"SWAP h")
        self.code.append(f"INC h")
        self.code.append(f"SWAP {divisor_register}")
        self.code.append(f"SUB {remainder_register}")
        self.code.append(f"SWAP {remainder_register}")
        self.code.append(f"SWAP {divisor_register}")
        
        
        
        # sprawdzeni czy trzebe rem = -rem
        self.code.append(f"SWAP h")
        self.code.append(f"JZERO 3")
        self.code.append(f"SWAP h")
        self.code.append(f"JUMP 5")
        self.code.append(f"RESET {quotient_register}")
        self.code.append(f"SUB {remainder_register}")
        self.code.append(f"SWAP {remainder_register}")
        self.code.append(f"SWAP h")
        
        self.code.append("RESET g")
        self.code.append("INC g")
        self.code.append("RESET h")
        self.code.append("DEC h")
        
        for i in range(start, end):
            self.code[i] = self.code[i].replace('midblock_start', str(midblock_start - i))
            self.code[i] = self.code[i].replace('block_FTL', str(block_FTL - i))
            self.code[i] = self.code[i].replace('block_PRE', str(block_PRE - i))
            self.code[i] = self.code[i].replace('end_div_INC_REM', str(end_div_INC_REM - i))
            self.code[i] = self.code[i].replace('end_div_ZERO_REM', str(end_div_ZERO_REM - i))
            self.code[i] = self.code[i].replace('end_div_INC', str(end_div_INC - i))
            self.code[i] = self.code[i].replace('end_div_ZERO', str(end_div_ZERO - i))
            self.code[i] = self.code[i].replace('end_div_TMP', str(end_div_TMP - i))
            self.code[i] = self.code[i].replace('end_div', str(end_div - i))
            self.code[i] = self.code[i].replace('koniec', str(end - i))
            self.code[i] = self.code[i].replace('minus', str(minus - i))
            self.code[i] = self.code[i].replace('check', str(check - i))
            self.code[i] = self.code[i].replace('correct', str(correct - i))
            self.code[i] = self.code[i].replace('minus_change', str(minus_change - i))
    
    def multiply_code(self, register_1, register_2, register_3, register_4, register_5):
        
        # czy pierwsza liczba zero
        self.code.append(f"RESET {register_5}")
        self.code.append(f"SWAP {register_2}")

        # ZASTANOW SIE GDZIE SKOK
        start = len(self.code)
        self.code.append(f"JZERO end") # na koniec 
        self.code.append(f"JPOS 5")
        self.code.append(f"INC {register_5}")
        self.code.append(f"RESET {register_2}")
        self.code.append(f"SWAP {register_2}")
        self.code.append(f"SUB {register_2}")
        self.code.append(f"SWAP {register_2}")
        #czy druga liczba zero
        self.code.append(f"SWAP {register_3}")
        start_2 = len(self.code)
        self.code.append(f"JZERO end") # na koniec 
        self.code.append(f"JPOS 5")
        self.code.append(f"DEC {register_5}")
        self.code.append(f"RESET {register_3}")
        self.code.append(f"SWAP {register_3}")
        self.code.append(f"SUB {register_3}")
        
        self.code.append(f"SWAP {register_3}")
        # czy czy a * b czy b * a
        self.code.append(f"RESET {register_1}")
        self.code.append(f"ADD {register_2}")
        self.code.append(f"SUB {register_3}")
        self.code.append(f"JNEG 23")  # prawa wieksza
    
        # a * b
        self.code.append(f"RESET {register_1}")
        self.code.append(f"SWAP {register_3}")
        self.code.append(f"JZERO 42") # na koniec potrzebny swap third
        self.code.append(f"SWAP {register_3}")
        self.code.append(f"RESET {register_4}")
        self.code.append(f"SWAP {register_4}")
        self.code.append(f"ADD {register_3}")
        self.code.append(f"SHIFT h")
        self.code.append(f"SHIFT g")
        self.code.append(f"SUB {register_3}")
        self.code.append(f"JZERO 4") # jesli  parzyste (0 na prawo) potrzebny swap na fourh
        self.code.append(f"SWAP {register_4}")# da sie rozbic na dwie czesci i lekka optymalizacja zamiast jump 2
        self.code.append(f"ADD {register_2}")
        self.code.append(f"JUMP 2")
        self.code.append(f"SWAP {register_4}")
        self.code.append(f"SWAP {register_3}")
        self.code.append(f"SHIFT h")
        self.code.append(f"SWAP {register_3}")    
        self.code.append(f"SWAP {register_2}")
        self.code.append(f"SHIFT g")
        self.code.append(f"SWAP {register_2}")
        self.code.append("JUMP -20")
    
        # b * a
        self.code.append(f"RESET {register_1}")
        self.code.append(f"SWAP {register_2}")
        self.code.append(f"JZERO 22") # na koniec potrzebny swap second
        self.code.append(f"SWAP {register_2}")
        self.code.append(f"RESET {register_4}")
        self.code.append(f"SWAP {register_4}")
        self.code.append(f"ADD {register_2}")
        self.code.append(f"SHIFT h")
        self.code.append(f"SHIFT g")
        self.code.append(f"SUB {register_2}")
        self.code.append(f"JZERO 4") # jesli parzyste (0 na prawo) potrzebny swap na fourh
        self.code.append(f"SWAP {register_4}")# da sie rozbic na dwie czesci i lekka optymalizacja zamiast jump 2
        self.code.append(f"ADD {register_3}")
        self.code.append(f"JUMP 2")
        self.code.append(f"SWAP {register_4}")
        self.code.append(f"SWAP {register_2}")
        self.code.append(f"SHIFT h")
        self.code.append(f"SWAP {register_2}")    
        self.code.append(f"SWAP {register_3}")
        self.code.append(f"SHIFT g")
        self.code.append(f"SWAP {register_3}")
        self.code.append("JUMP -20")
        # koniec
        self.code.append(f"SWAP {register_3}")
        self.code.append(f"JUMP 2")
        self.code.append(f"SWAP {register_2}")
        # czy liczba ujemna
        self.code.append(f"SWAP {register_5}")
        self.code.append(f"JZERO 4")
        self.code.append(f"RESET {register_1}")
        self.code.append(f"SUB {register_5}")
        self.code.append(f"JUMP 2")
        self.code.append(f"SWAP {register_5}")
        end = len(self.code)
                
        for i in range(start, end):
            self.code[i] = self.code[i].replace('end', str(end - i))
                
    def num_condition(self, condition):
        # jesli obie wartosci sa z gory znane
        if condition[1][0] == "num" and condition[2][0] == "num":
            if condition[0] == "EQ":
                return condition[1][1] == condition[2][1]
            elif condition[0] == "NEQ":
                return condition[1][1] != condition[2][1]
            elif condition[0] == "LEQ":
                return condition[1][1] <= condition[2][1]
            elif condition[0] == "LE":
                return condition[1][1] < condition[2][1]
            elif condition[0] == "GEQ":
                return condition[1][1] >= condition[2][1]
            elif condition[0] == "GE":
                return condition[1][1] > condition[2][1]

        elif condition[1] == condition[2]:
            if condition[0] in ["EQ", "GEQ", "LEQ"]:
                return True
            else:
                return False
        

    def solve_condition(self, condition, register_1='a', register_2='b', register_3='c'):
        if condition[1][0] == "num" and condition[1][1] == 0:
            self.solve(condition[2], register_1, register_2)
            if condition[0] == "EQ":
                self.code.append(f"JZERO 2")
                self.code.append("JUMP if_mark")
            elif condition[0] == "NEQ":
                self.code.append(f"JZERO if_mark")
            elif condition[0] == "LE":
                self.code.append(f"JNEG 2")
                self.code.append("JUMP if_mark")
            elif condition[0] == "LEQ":
                self.code.append(f"JPOS if_mark") 
            elif condition[0] == "GE":
                self.code.append(f"JPOS 2") 
                self.code.append("JUMP if_mark")
            elif condition[0] == "GEQ":
                self.code.append(f"JNEG if_mark") 

        elif condition[2][0] == "num" and condition[2][1] == 0:
            self.solve(condition[1], register_1, register_2)
            if condition[0] == "EQ":
                self.code.append(f"JZERO 2")
                self.code.append("JUMP if_mark")
            elif condition[0] == "NEQ":
                self.code.append(f"JZERO if_mark")
            elif condition[0] == "LEQ":
                self.code.append(f"JPOS if_mark") 
            elif condition[0] == "LE":
                self.code.append(f"JNEG 2")
                self.code.append("JUMP if_mark")
            elif condition[0] == "GEQ":
                self.code.append(f"JNEG if_mark") 
            elif condition[0] == "GE":
                self.code.append(f"JPOS 2") 
                self.code.append("JUMP if_mark")


        else:
            self.solve(condition[1], register_1, register_3)
            self.solve(condition[2], register_2, register_3)
            
            if condition[0] == "EQ":
                self.code.append(f"SUB {register_2}")
                self.code.append(f"JZERO 2")
                self.code.append("JUMP if_mark")
            elif condition[0] == "NEQ":
                self.code.append(f"SUB {register_2}")
                self.code.append(f"JZERO if_mark")
            elif condition[0] == "LEQ":
                self.code.append(f"SUB {register_2}")
                self.code.append(f"JPOS if_mark")
            elif condition[0] == "LE":
                self.code.append(f"SUB {register_2}")
                self.code.append(f"JNEG 2")
                self.code.append("JUMP if_mark")
            elif condition[0] == "GEQ":
                self.code.append(f"SUB {register_2}")
                self.code.append(f"JNEG if_mark")
            elif condition[0] == "GE":
                self.code.append(f"SUB {register_2}")
                self.code.append(f"JPOS 2") 
                self.code.append("JUMP if_mark")


    # warttosc pod wskazanym indexem na reg1
    def load_arr(self, array, index, reg1, reg2):
        self.load_arr_pointer(array, index, reg1, reg2)
        self.code.append(f"SWAP {reg1}")
        self.code.append(f"LOAD a")
        self.code.append(f"SWAP {reg1}")

    #czesto pseudo pierwszy rejestr
    # addres w rejestrze reg1
    def load_arr_pointer(self, array, idx, register_1, register_2):
        #jesli num
        if type(idx) == int:
            # TODO zabezpiecz dostep do array bez pozwolenia
            address = self.symbol_table.get_pointer((array, idx))
            self.get_num(address, register_1)
        elif type(idx) == tuple:
            
            if idx[0] == 'undeclared':
                raise Exception(f"SHOULD NEVER RAISED")
            # wartosc indexu w reg1
            self.load_var(idx[1], register_1)
            # zwraca array
            var = self.symbol_table.get_var(array)
            # poczatkowy index array w reg2
            self.get_num(var.first_idx, register_2)
            # patrzymy ktory z kolei to jest element o tym indexie
            self.code.append(f"SWAP {register_1}")
            self.code.append(f"SUB {register_2}")
            # dodajemy od kiedy sie zaczyna array
            self.get_num(var.max_memory, register_2)
            self.code.append(f"ADD {register_2}")
            self.code.append(f"SWAP {register_1}")

    # pod zadanym rejestrem bedzie wartosc zmiennej
    def load_var(self, var_name, register_1):
        if self.iterators and var_name == self.iterators[-1]:
            self.code.append(f"RESET {register_1}")
            self.code.append(f"SWAP {register_1}")
            self.code.append(f"ADD f")
            self.code.append(f"SWAP {register_1}")
        else:
            self.load_var_pointer(var_name, register_1)
            self.code.append(f"SWAP {register_1}")
            self.code.append(f"LOAD a")
            self.code.append(f"SWAP {register_1}")

    # pod zadanym rejestrem jest adres name
    def load_var_pointer(self, var_name, register_1):
        if  var_name in self.iterators or (type(self.symbol_table[var_name]) == Variable and self.symbol_table[var_name].initialized):
            pointer = self.symbol_table.get_pointer(var_name)
            self.get_num(pointer, register_1)
        else:
            raise Exception(f"Unknown variable {var_name}/ not init")

    def load_iter(self, iter_name, register_1):
        self.load_var_pointer(iter_name, register_1)
        self.code.append(f"SWAP {register_1}")
        self.code.append(f"LOAD a")
        self.code.append(f"SWAP {register_1}")

    # pod zadanym rejestrem jest adres name
    def load_iter_pointer(self, iter_name, register_1):
        if type(self.symbol_table[iter_name]) == Iter and iter_name in self.symbol_table:
            pointer = self.symbol_table.get_pointer(iter_name)
            self.get_num(pointer, register_1)
        else:
            raise Exception(f"Unknown iter {iter_name}/  not init")