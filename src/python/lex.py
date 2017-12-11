
import sys
import ply.lex



class LexLogger(object):
    def __init__(self, f):
        self.f = f
        # assert False

    def dolog(self, msg, *args, **kwargs):
        self.f.write((msg % args) + '\n')
        # assert False
        return
    def critical(self, msg, *args, **kwargs):
        self.f.write((msg % args) + '\n')
        # assert False
        return

    def warning(self, msg, *args, **kwargs):
        self.f.write('WARNING: ' + (msg % args) + '\n')
        # assert False
        return

    def error(self, msg, *args, **kwargs):
        self.f.write('ERROR: ' + (msg % args) + '\n')
        # assert False

    info = dolog
    debug = dolog


class Lexer:
    keywords = ('trait', 'class', 'import', 'func', 'var', 'package', 'enum','interface', 'typedef', 'const',
        'if', 'else', 'elseif', 'while', 'for', 'do', 'continue', 'break', 'return', 'of', 'case', 'default',
        'in', 'this', 'is', 'as', 
        'and', 'or', 'not', 'xor',
        'nil', 'void',
        # 'char', 'float', 'double', 'string', 
        # 'byte', 'sbyte', 'bool', 'true', 'false',
        # 'short', 'ushort', 'int', 'uint', 'long', 'ulong', 'uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64',
        'extension', 'using',
        'template'
        )

    keyword_tokens = tuple(map(str.upper, keywords))
    tokens = keyword_tokens + (

      # Literals (identifier, integer constant, float constant, string constant, char const)
      'ID', 'TYPEID', 'ICONST10', 'ICONST16', 'ICONST8', 'FCONST', 'SCONST', 'CCONST',

      # Operators (+,-,*,/,%,|,&,~,^,<<,>>, ||, &&, !, <, <=, >, >=, ==, !=)
      'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
      'BOR', 'BAND', 'BNOT', 'BXOR', 'LSHIFT', 'RSHIFT',
      #'LOR', 'LAND', 'LNOT',
      'LT', 'LE', 'GT', 'GE', 'EQ', 'NE', 'TRANSFORM',
      
      # Assignment (=, *=, /=, %=, +=, -=, <<=, >>=, &=, ^=, |=)
      'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL',
      'LSHIFTEQUAL','RSHIFTEQUAL', 'ANDEQUAL', 'XOREQUAL', 'OREQUAL',
      #'DECIMAL', 'DOLLAR',
      'DOLLAR_NUMBER',# 'NUMBER',
      #'INFER',

      # Increment/decrement (++,--)
      #'PLUSPLUS', 'MINUSMINUS',

      # Structure dereference (->)
      #'ARROW',

      # Conditional operator (?)
      #'CONDOP',
      
      # Delimeters ( ) [ ] { } , . ; :
      'LPAREN', 'RPAREN',
      'LBRACKET', 'RBRACKET',
      'LBRACE', 'RBRACE',
      #'L_ANGLE_BRACKET', 'R_ANGLE_BRACKET',
      'COMMA', 'PERIOD', 'SEMI', 'COLON', 'ATSIGN',
      'NEWLINE', 'DOUBLE_COLON', 'HASH', 'DOLLAR', 'BACK_QUOTE', 'THREE_BACK_QUOTE'
    #   'UMINUS', 'UPLUS',

      #'SHIFT_OP', 'COMPARE_OP'
      )

    #t_INFER        = r'\->'
    # Operators
    t_PLUS             = r'\+'
    t_MINUS            = r'\-'
    # t_UPLUS            = r'\+'
    # t_UMINUS           = r'\-'
    t_TIMES            = r'\*'
    t_DIVIDE           = r'\/'
    t_MOD              = r'\%'
    t_BOR               = r'\|'
    t_BAND              = r'\&'
    t_BNOT              = r'\~'
    t_BXOR              = r'\^'
    t_LSHIFT           = r'<<'
    t_RSHIFT           = r'>>'
    t_LT               = r'<'
    t_GT               = r'>'
    t_LE               = r'<='
    t_GE               = r'>='
    t_EQ               = r'=='
    t_NE               = r'!='

    # Assignment operators

    t_EQUALS           = r'='
    t_TIMESEQUAL       = r'\*='
    t_DIVEQUAL         = r'/='
    t_MODEQUAL         = r'%='
    t_PLUSEQUAL        = r'\+='
    t_MINUSEQUAL       = r'-='
    t_LSHIFTEQUAL      = r'<<='
    t_RSHIFTEQUAL      = r'>>='
    t_ANDEQUAL         = r'&='
    t_OREQUAL          = r'\|='
    t_XOREQUAL         = r'^='
    t_HASH             = r'\#'
    #t_INFER            = r'eq'
    t_DOLLAR           = r'\$'
    t_BACK_QUOTE       = r'\`'
    t_THREE_BACK_QUOTE = r'\`\`\`'


    # Increment/decrement
    #t_PLUSPLUS         = r'\+\+'
    #t_MINUSMINUS       = r'--'

    # ->
    #t_ARROW            = r'->'

    # ?
    #t_CONDOP           = r'\?'

    # Delimeters
    #t_L_ANGLE_BRACKET           = r'\<'
    #t_R_ANGLE_BRACKET           = r'\>'
    t_LPAREN           = r'\('
    t_RPAREN           = r'\)'
    t_LBRACKET         = r'\['
    t_RBRACKET         = r'\]'
    t_LBRACE           = r'\{'
    t_RBRACE           = r'\}'
    t_COMMA            = r','
    t_PERIOD           = r'\.'
    t_SEMI             = r';'
    t_COLON            = r':'
    t_DOUBLE_COLON     = r'::'
    t_ATSIGN           = r'@'
    t_TRANSFORM        = r'=>'

    def t_comment(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')

    def t_linecomment(self, t):
        r'//(.)*'
        t.lexer.lineno += 1

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        # print("t_ID", t, t.value, t.lineno, t.type)
        if t.value in Lexer.keywords:
            t.type = t.value.upper()
            # print("t_ID keyword", t, t.value, t.lineno, t.type)
        return t

    def t1_NUMBER1(self, t):
        r'\d+'
        try:
            t.value = int(t.value)
        except ValueError:
            print "Integer value too large", t.value
            t.value = 0
        return t

    def at_DECIMAL(self, t):
        r'\d+'
        try:
            value = int(t.value)
        except e as ValueError:
            print "t_DECIMAL: Integer value too large", t.value
            # t.value = 0
            raise e
        # print('t_DECIMAL', t, t.value, type(t.value))
        return t

    def t_DOLLAR_NUMBER(self, t):
        r'\$\d+'
        # print('t_DOLLAR_NUMBER start', t, t.value, type(t.value))
        try:
            t.value = int(t.value[1:])
        except ValueError, e:
            print "Integer value too large", t.value
            # t.value = 0
            raise e
        # print('t_DOLLAR_NUMBER', t, t.value, type(t.value))
        return t

    # Ignored characters
    t_ignore = " \t"

    #t_ignore_NEWLINE = '\n'

    # Integer literal
    t_ICONST10 = r'(\d+)([uU]|[lL]|[uU][lL]|[lL][uU]|LL)?'
    t_ICONST16 = r'0[xX]([0-9a-fA-F]+)([uU]|[lL]|[uU][lL]|[lL][uU]|LL)?'
    t_ICONST8 = r'0[0-7]+([uU]|[lL]|[uU][lL]|[lL][uU]|LL)?'

    # Floating literal
    t_FCONST = r'((\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))([lL]|[fF])?'

    # Floating literal
    t1_NUMBER11 = r'\d+'

    # String literal
    t_SCONST = r'\"([^\\\n]|(\\.))*?\"'

    # Character constant 'c' or L'c'
    #t_CCONST = r'(L)?\'([^\\\n]|(\\.))*?\''
    t_CCONST = r'\'([^\\\n]|(\\.))\''

    #t_TRUE = r'true'
    #t_FALSE = r'false'
    #t_NIL = r'nil'

    def at_COMPARE_OP(self, t):
        r'>=|<=|!=|==|<|>'
        return t

    def at_SHIFT_OP(self, t):
        r'<<|>>'
        return t

    def t_newline(self, t):
        r'(\r\n)|\r|\n'
        t.lexer.lineno += 1
        t.type = 'NEWLINE'
        return t

    def t_error(self, t):
        print "Illegal character '%s'" % t.value[0]
        #t.lexer.skip(1)
        assert False, (self, t, t.value)
    def build(self, **kwargs):
        #print("build", ply)
        #print("ply.lex", dir(ply.lex))
        #print("ply.lex.lex", dir(ply.lex.lex))
        self.lexer = ply.lex.lex(lextab='gmllextab', module=self, optimize=False, debug=False, **kwargs)
    def __init__(self):
        self.lexer = None




