from sly import Lexer, Parser
from handler import Handler
from structures import Array, Variable, SymbolTable, Iter
import ast

class Lex(Lexer):
    
    tokens = {
		PLUS, MINUS, TIMES, DIV, MOD,
		NEQ, EQ, LEQ, GEQ, LE, GE, 
		ASSIGN,
		FOR, FROM, TO, DOWNTO, DO, ENDFOR,
		READ, WRITE,
		WHILE, ENDWHILE,
		IF, THEN, ELSE, ENDIF,
		REPEAT, UNTIL,
		VAR, BEGIN, END,
        SEM, LBRACKET, COLON, RBRACKET, COMMA,
        PIDENTIFIER, NUM

    }
    
    
    PLUS = r'PLUS'
    MINUS = r'MINUS'
    TIMES = r'TIMES'
    DIV = r'DIV'
    MOD = r'MOD'
    
    NEQ = r'NEQ'
    EQ = r'EQ'
    LEQ = r'LEQ'
    GEQ = r'GEQ'
    LE = r'LE'
    GE = r'GE'

    ASSIGN = r'ASSIGN'

    FOR = r'FOR'
    FROM = r'FROM'
    TO = r'TO'
    DOWNTO = r'DOWNTO'
    DO = r'DO'
    ENDFOR = r'ENDFOR'

    READ = r'READ'
    WRITE = r'WRITE'

    WHILE = r'WHILE'
    ENDWHILE = r'ENDWHILE'

    IF = r'IF'
    THEN = r'THEN'
    ELSE = r'ELSE'
    ENDIF = r'ENDIF'

    REPEAT = r'REPEAT'
    UNTIL = r'UNTIL'

    VAR = r'VAR'
    BEGIN = r'BEGIN'
    END = r'END'

    SEM = r';'
    COLON = r':'
    COMMA = r','
    LBRACKET = r'\['
    RBRACKET = r'\]'
    
    PIDENTIFIER = r'[_a-z]+'

    ignore = ' \t'

    @_(r'[-]?\d+')
    def NUM(self, t):
        t.value = int(t.value)
        return t

    @_(r'\([^\)]*\)')
    def ignore_comment(self, t):
        self.lineno += t.value.count('\n')
    
    @_(r'\n+')
    def ignore_empty(self, t):
        self.lineno += len(t.value)


    def error(self, t):
        Exception(f'{self.lineno} line: ERROR LEXER')


class Par(Parser):
    tokens = Lex.tokens
    symbol_table = SymbolTable()
    code = None
    actual_line = 0

    @_('VAR declarations BEGIN commands END', 'BEGIN commands END')
    def program(self, p):
        self.code = Handler(p.commands, self.symbol_table)
        return self.code

    @_('declarations COMMA PIDENTIFIER')
    def declarations(self, p):
        try:
            self.symbol_table.add_var(p[-1])
        except Exception as e:
            raise Exception(f"{p.lineno} line: {e}")
    
    @_('PIDENTIFIER')
    def declarations(self, p):
        self.symbol_table.add_var(p[-1])
        
    @_('declarations COMMA PIDENTIFIER LBRACKET NUM COLON NUM RBRACKET')
    def declarations(self, p):
        try:
            self.symbol_table.add_arr(p[2], p[4], p[6])
        except Exception as e:
            raise Exception(f"{p.lineno} line: {e}")
        
    @_('PIDENTIFIER LBRACKET NUM COLON NUM RBRACKET')
    def declarations(self, p):
        self.symbol_table.add_arr(p[0], p[2], p[4])
        
    @_('commands command')
    def commands(self, p):
        return p[0] + [p[1]]

    @_('command')
    def commands(self, p):
        return [p[0]]
        
        
    @_('identifier ASSIGN expression SEM')
    def command(self, p):
        command = "ASSIGN", p[0], p[2]
        return command, p.lineno

    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        command = "IFELSE", p[1], p[3], p[5]
        return command, p.lineno
        
    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        command = "IF", p[1], p[3]
        return command, p.lineno

    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        command = "WHILE", p[1], p[3]
        return command, p.lineno

    @_('REPEAT commands UNTIL condition SEM')
    def command(self, p):
        command = "REPEAT", p[3], p[1]
        return command, p.lineno
    
        
    @_('FOR PIDENTIFIER FROM value TO value DO commands ENDFOR')
    def command(self, p):
        tasks = str(p[7]).replace("('undeclared', '" + p[1] + "')", "'" + str(p[1]) + "'")
        tasks = ast.literal_eval(tasks)
        command = "FORTO", p[1], p[3], p[5], tasks
        return command, p.lineno

    @_('FOR PIDENTIFIER FROM value DOWNTO value DO commands ENDFOR')
    def command(self, p):
        tasks = str(p[7]).replace("('undeclared', '" + p[1] + "')", "'" + str(p[1]) + "'")
        tasks = ast.literal_eval(tasks)
        command = "FORDOWN", p[1], p[3], p[5], tasks
 
        return command, p.lineno
        
    @_('READ identifier SEM')
    def command(self, p):
        command = "READ", p[1]
        return command, p.lineno


    @_('WRITE value SEM')
    def command(self, p):
        command = "WRITE", p[1]
        return command, p.lineno

    @_('value')
    def expression(self, p):
        command = p[0]
        return command

    @_('value PLUS value')
    def expression(self, p):
        command = "PLUS", p[0], p[2]
        return command

    @_('value MINUS value')
    def expression(self, p):
        command ="MINUS", p[0], p[2]
        return command

    @_('value TIMES value')
    def expression(self, p):
        command = "TIMES", p[0], p[2]
        return command

    @_('value DIV value')
    def expression(self, p):
        command = "DIV", p[0], p[2]
        return command

    @_('value MOD value')
    def expression(self, p):
        command = "MOD", p[0], p[2]
        return command
    
    @_('value NEQ value')
    def condition(self, p):
        command = "NEQ", p[0], p[2]
        return command
    
    @_('value EQ value')
    def condition(self, p):
        command = "EQ", p[0], p[2]
        return command

    @_('value LEQ value')
    def condition(self, p):
        command = "LEQ", p[0], p[2]
        return command

    @_('value GEQ value')
    def condition(self, p):
        command = "GEQ", p[0], p[2]
        return command
    
    @_('value LE value')
    def condition(self, p):
        command = "LE", p[0], p[2]
        return command

    @_('value GE value')
    def condition(self, p):
        command = "GE", p[0], p[2]
        return command

    @_('NUM')
    def value(self, p):
        command = "num", p[0]
        return command

    @_('identifier')
    def value(self, p):
        command = "LOAD", p[0]
        return command

    @_('PIDENTIFIER')
    def identifier(self, p):
        
        if p[0] in self.symbol_table or p[0] in self.symbol_table.iterators:
            return p[0]
        else:
            return "undeclared", p[0]
        
    @_('PIDENTIFIER LBRACKET PIDENTIFIER RBRACKET')
    def identifier(self, p):
        if p[0] in self.symbol_table and type(self.symbol_table[p[0]]) == Array:
            if p[2] in self.symbol_table and type(self.symbol_table[p[2]]) == Variable:
                return "array", p[0], ("load", p[2])
            else:
                return "array", p[0], ("load", ('undeclared', p[2]))
        else:
            raise Exception(f"{p.lineno} Unknow array {p[0]}")

    @_('PIDENTIFIER LBRACKET NUM RBRACKET')
    def identifier(self, p):
        if p[0] in self.symbol_table and type(self.symbol_table[p[0]]) == Array:
            return "array", p[0], p[2]
        else:
            raise Exception(f"{p.lineno} Unknow array {p[0]}")
                  

    def error(self, token):
        raise Exception(f"{token.lineno} line: ERROR PARSER {token}")
        
        
if __name__ == '__main__':
    lex = Lex()
    pars = Par()
    
    with open('test.txt') as in_f:
        text = in_f.read()

    pars.parse(lex.tokenize(text))
    code_gen = pars.code
    try:
        dupa = code_gen.start()
    except Exception as e:
       raise Exception(f"{code_gen.symbol_table.line_counter} line : {e}")

    dupa = [x+"\n" for x in dupa]
    
    with open('./wirtualna/maszyna_wirtualna/test_out.mr', 'w') as in_f:
        pass
    with open('./wirtualna/maszyna_wirtualna/test_out.mr', 'a') as in_f:
        text = in_f.writelines(dupa)