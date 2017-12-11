import sys
import ply.lex
import ply.yacc
from lex import LexLogger
import traceback
from ast import *

class GoLexer:
    keywords = ('func', 'var', 'package', 'interface', 'type', 'const',
        'void',
        'nil', 'true', 'false',
        'char', 'float', 'double', 'string', 
        'byte', 'sbyte', 'bool', 
        'short', 'ushort', 'int', 'uint', 'long', 'ulong', 'uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64',
        'continue', 'break', 'import',
        'map', 'struct', 'chan',
        )

    keyword_tokens = tuple(map(str.upper, keywords))
    tokens = keyword_tokens + (

      # Literals (identifier, integer constant, float constant, string constant, char const)
      'ID', 'TYPEID', 'ICONST10', 'ICONST16', 'ICONST8', 'FCONST', 'SCONST', 'CCONST', 'CCONST_UNICODE', 'CCONST_HEX',

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
      'AND', 'OR', 'NOT',
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
      'NEWLINE', 'DOUBLE_COLON', 'HASH', 'DOLLAR',
      'ELLIPSIS',
      'CHAN_DIR',
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
    t_NOT               = r'!'
    t_AND               = r'&&'
    t_OR               = r'\|\|'

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
    t_DOLLAR         = r'\$'


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
    t_ELLIPSIS         = r'\.\.\.'
    t_CHAN_DIR         = r'\<\-'

    def t_comment(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')

    def t_linecomment(self, t):
        r'//(.)*'
        t.lexer.lineno += 1

    def at_godoc(self, t):
        # r'\n(.)*'
        t.lexer.lineno += 1
        # discard

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        # print('t_ID', t, t.value, t.lineno, t.type)
        if t.value in GoLexer.keywords:
            t.type = t.value.upper()
            # print('t_ID keyword', t, t.value, t.lineno, t.type)
        return t

    def t1_NUMBER1(self, t):
        r'\d+'
        try:
            t.value = int(t.value)
        except ValueError:
            print 'Integer value too large', t.value
            t.value = 0
        return t

    def at_DECIMAL(self, t):
        r'\d+'
        try:
            value = int(t.value)
        except e as ValueError:
            print 't_DECIMAL: Integer value too large', t.value
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
            print 'Integer value too large', t.value
            # t.value = 0
            raise e
        # print('t_DOLLAR_NUMBER', t, t.value, type(t.value))
        return t

    # Ignored characters
    t_ignore = ' \t'

    #t_ignore_NEWLINE = '\n'

    # Integer literal
    # t_ICONST = r'\d+([uU]|[lL]|[uU][lL]|[lL][uU]|LL)?'
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
    t_CCONST = r"'([^\\\n]|(\\.))'"
    # t_CCONST_UNICODE = r"'\\[Uu][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]'"
    t_CCONST_UNICODE = r"'\\[Uu][0-9a-fA-F]{4}([0-9a-fA-F]{4})?'"
    t_CCONST_HEX = r"'\\[Xx][0-9a-fA-F]{2}'"

    # Character constant 'c' or L'c'
    #t_CCONST = r'(L)?\'([^\\\n]|(\\.))*?\''
    at_ANYTEXT = r'[^ \t]([^\\\n]|(\\.))*?'

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
        print 'Illegal character "%s"' % t.value[0]
        #t.lexer.skip(1)
        assert False, (self, t, t.value)
    def build(self, **kwargs):
        #print('build', ply)
        #print('ply.lex', dir(ply.lex))
        #print('ply.lex.lex', dir(ply.lex.lex))
        self.lexer = ply.lex.lex(lextab='golextab', module=self, optimize=False, debug=False, **kwargs)
    def __init__(self):
        self.lexer = None


class GoParser(object):
    # dictionary of names
    tokens = GoLexer.tokens

    def p_go_identifier(self, t):
        'go_identifier : ID'
        # print('identifier: ID', t[1])
        t[0] = Identifier(t[1])

    def p_go_ext_idstr(self, t):
        '''go_ext_idstr : ID
                     | go_builtin_idstr
                     '''
        t[0] = t[1]
    def p_go_builtin_idstr(self, t):
        '''go_builtin_idstr : IMPORT
                            | CONTINUE
                            | BREAK
                            '''
        t[0] = t[1]
    def p_go_ext_identifier(self, t):
        '''go_ext_identifier : ID
                             | go_builtin_idstr
                             '''
        t[0] = Identifier(t[1])

    def p_go_type_specifier(self, t):
        '''go_type_specifier : CHAR
                          | BYTE
                          | SBYTE
                          | SHORT
                          | USHORT
                          | INT
                          | UINT
                          | LONG
                          | ULONG
                          | INT8
                          | INT16
                          | INT32
                          | INT64
                          | UINT8
                          | UINT16
                          | UINT32
                          | UINT64
                          | FLOAT
                          | DOUBLE
                          | STRING
                          | BOOL
                          '''
        t[0] = t[1]
    def p_go_id_path_1(self, t):
        'go_id_path : ID'
        t[0] = [t[1]]
    def p_go_id_path_2(self, t):
        'go_id_path : go_id_path PERIOD ID'
        # print('id_path_2', t, list(t))
        t[0] = t[1] + [t[3]]

    def p_primary(self, t):
        '''primary : atom
                   | attribute_ref
                   | call
                   | paren_expr
                   '''
        # print('primary', t, t[1])
        t[0] = t[1]

    def p_primary_ref(self, t):
        'primary : BAND atom'
        t[0] = t[2]

    def p_attribute_ref(self, t):
        'attribute_ref : primary PERIOD go_ext_idstr'
        t[0] = AttrRef(t[1], t[3])

    def p_expr_list(self, t):
        'expr_list : go_expr'
        t[0] = [t[1]]

    def p_expr_list_1(self, t):
        'expr_list : expr_list COMMA go_expr'
        t[0] = t[1] + [t[3]]

    def p_call(self, t):
        'call : primary LPAREN expr_list RPAREN'
        t[0] = Call(t[1], t[3])

    def p_call_empty(self, t):
        'call : primary LPAREN RPAREN'
        t[0] = Call(t[1], [])

    def p_paren_expr(self, t):
        'paren_expr : LPAREN go_expr RPAREN'
        t[0] = t[2]

    def p_atom(self, t):
        'atom : go_identifier'
        # print('atom:identifier', t[0], t[1])
        t[0] = t[1]

    def p_atom_literal(self, t):
        'atom : literal'
        #print('atom:literal', t[0], t[1])
        t[0] = t[1]

    def p_literal_nil(self, t):
        'literal : NIL'
        # print('literal-nil', t[1], type(t[1]), len(t[1]))
        t[0] = Nil()
    def p_string_literal(self, t):
        'literal : SCONST'
        # print('p_string_literal', t[1], type(t[1]), len(t[1]))
        text = t[1][1:-1]
        t[0] = StringLiteral(text)
    def p_literal_true(self, t):
        'literal : TRUE'
        t[0] = BoolLiteral('true', value=True)
    def p_literal_false(self, t):
        'literal : FALSE'
        t[0] = BoolLiteral('false', value=False)
    def p_literal_map(self, t):
        'literal : MAP LBRACKET go_type RBRACKET go_type LBRACE maybe_newlines go_map_item_list maybe_newlines RBRACE'
        t[0] = DictLiteral(t[7])
    def p_literal_map_2(self, t):
        'literal : MAP LBRACKET go_type RBRACKET go_type LBRACE maybe_newlines go_map_item_list COMMA maybe_newlines RBRACE'
        t[0] = DictLiteral(t[7])
    def p_literal_map_empty(self, t):
        'literal : MAP LBRACKET go_type RBRACKET go_type LBRACE maybe_newlines RBRACE'
        t[0] = DictLiteral([])

    def p_literal_list(self, t):
        'literal : list_literal'
        t[0] = t[1]

    def p_map_item(self, t):
        'go_map_item : go_expr COLON go_expr'
        t[0] = DictItem(t[1], t[3])

    def p_map_item_list_1(self, t):
        'go_map_item_list : go_map_item maybe_newlines'
        t[0] = [t[1]]
        # print('p_map_item_list_1', list(t))
    def p_map_item_list_2(self, t):
        'go_map_item_list : go_map_item_list COMMA maybe_newlines go_map_item'
        t[0] = t[1] + [t[4]]
        # print('p_map_item_list_2', list(t))

    def p_multilined_expr_list_1(self, t):
        'multilined_expr_list : go_expr maybe_newlines COMMA maybe_newlines go_expr maybe_newlines'
        # print('p_expr_list_1', list(t))
        t[0] = [t[1], t[5]]

    def p_multilined_expr_list_2(self, t):
        'multilined_expr_list : multilined_expr_list COMMA maybe_newlines go_expr maybe_newlines'
        # print('p_expr_list_2', list(t))
        t[0] = t[1] + [t[4]]
    def p_multilined_many_expr_list_1(self, t):
        'many_multilined_expr_list : multilined_expr_list COMMA maybe_newlines go_expr maybe_newlines'
        # print('p_many_expr_list_1', list(t))
        t[0] = t[1] + [t[4]]

    def p_list_literal(self, t):
        'list_literal : LBRACKET RBRACKET go_type LBRACE multilined_expr_list maybe_comma RBRACE'
        t[0] = ListLiteral(t[5])

    def p_list_literal_1(self, t):
        'list_literal : LBRACKET RBRACKET go_type LBRACE newlines multilined_expr_list maybe_comma RBRACE'
        t[0] = ListLiteral(t[6])

    def p_literal_list_2(self, t):
        'list_literal : LBRACKET RBRACKET go_type LBRACE go_expr maybe_newlines maybe_comma RBRACE'
        t[0] = ListLiteral([t[5]])

    def p_literal_list_3(self, t):
        'list_literal : LBRACKET RBRACKET go_type LBRACE newlines go_expr maybe_newlines maybe_comma RBRACE'
        t[0] = ListLiteral([t[6]])

    def p_literal_empty_list(self, t):
        'list_literal : LBRACKET RBRACKET go_type LBRACE maybe_newlines RBRACE'
        t[0] = ListLiteral([])

    def p_maybe_comma(self, t):
        'maybe_comma : COMMA maybe_newlines'
        t[0] = t[1]

    def p_maybe_comma_none(self, t):
        'maybe_comma : '
        t[0] = None

    def p_number(self, t):
        'number : ICONST10'
        t[0] = IntLiteral(t[1], int(t[1]))
        assert not isinstance(t[0], str), (t[0], type(t[0]))
        # print('p_number', t[1], t[0])

    def p_number_2(self, t):
        'number : ICONST16'
        s = t[1][2:]
        t[0] = IntLiteral(s, int(s, 16))
        assert not isinstance(t[0], str), (t[0], type(t[0]))
        # print('p_number_2', t[1], t[0])

    def p_number_3(self, t):
        'number : ICONST8'
        s = t[1][1:]
        t[0] = IntLiteral(s, int(s, 8))
        assert not isinstance(t[0], str), (t[0], type(t[0]))
        # print('p_number_3', t[1], t[0])

    def p_literal_integer(self, t):
        'literal : number'
        # print('p_literal_integer', t[1])
        assert not isinstance(t[1], str), (t[1], type(t[1]))
        t[0] = t[1]

    def p_literal_float(self, t):
        'literal : FCONST'
        t[0] = FloatLiteral(t[1], float(t[1]))

    def p_literal_char(self, t):
        'literal : CCONST'
        t[0] = CharLiteral(t[1][1:-1])

    def p_literal_char_unicode(self, t):
        'literal : CCONST_UNICODE'
        t[0] = CharLiteral(t[1][1:-1])

    def p_literal_char_hex(self, t):
        'literal : CCONST_HEX'
        t[0] = CharLiteral(t[1][1:-1])

    def p_go_ext_id_path_1(self, t):
        'go_ext_id_path : go_ext_idstr'
        t[0] = [t[1]]
    def p_go_ext_id_path_2(self, t):
        'go_ext_id_path : go_ext_id_path PERIOD go_ext_idstr'
        # print('id_path_2', t, list(t))
        t[0] = t[1] + [t[3]]


    def p_go_expr(self, t):
        'go_expr : unary_expr'
        t[0] = t[1]

    def ap_go_expr_0(self, t):
        # 'go_expr : BAND atom'
        t[0] = t[2]

    def p_go_expr_1(self, t):
        'go_expr : go_expr binary_op go_expr'
        t[0] = BinaryOp(t[2], t[1], t[3])

    def p_unary_expr(self, t):
        'unary_expr : unary_op unary_expr'
        t[0] = UnaryOp(t[1], t[2])

    def p_unary_expr_1(self, t):
        'unary_expr : primary'
        t[0] = t[1]

    def ap_unary_expr_2(self, t):
        # 'unary_expr : BAND primary'
        t[0] = t[2]

    def p_unary_op(self, t):
        '''unary_op : PLUS
                    | MINUS
                    | NOT'''
        t[0] = t[1]

    def p_binary_op(self, t):
        '''binary_op : PLUS
                     | MINUS
                     | TIMES
                     | DIVIDE
                     | MOD
                     | LSHIFT
                     | RSHIFT
                     | EQ
                     | NE
                     | LT
                     | GT
                     | LE
                     | GE
                     | AND
                     | OR
                     | BOR
                     | BXOR
                     '''
                    #  | BAND
        t[0] = t[1]


    def p_go_type_void(self, t):
        'go_type : VOID'
        t[0] = makePrimitiveType('void')
    def p_go_type_1(self, t):
        'go_type : go_type_specifier'
        t[0] = makePrimitiveType(t[1])
    def p_go_type_0(self, t):
        'go_type : go_id_path'
        t[0] = UserType(t[1])
    def p_go_type_array(self, t):
        'go_type : LBRACKET RBRACKET go_type'
        # t[0] = ArrayType(t[3], -1)
        # assert False, list(t)
        # t[0] = UserType(['Array'], [GenericTypeArg(t[3]), GenericLiteralArg(None)])
        t[0] = createListType(t[3])
    def p_go_type_array_size(self, t):
        'go_type : LBRACKET number RBRACKET go_type'
        # t[0] = ArrayType(t[4], int(t[2]))
        t[0] = createListType(t[4])
        # t[0] = UserType(['Array'], [GenericTypeArg(t[4]), GenericLiteralArg(IntLiteral(t[2], int(t[2])))])
    def p_go_type_pointer(self, t):
        'go_type : TIMES go_type'
        t[0] = PointerType(t[2])
    def p_go_type_chan(self, t):
        'go_type : CHAN go_type'
        t[0] = createListType(t[2])
    def p_go_type_chan_receiver(self, t):
        'go_type : CHAN_DIR CHAN go_type'
        t[0] = createListType(t[3])
    def p_go_type_chan_sender(self, t):
        'go_type : CHAN CHAN_DIR go_type'
        t[0] = createListType(t[3])

    def p_go_type_dict(self, t):
        'go_type : MAP LBRACKET go_type RBRACKET go_type'
        # print('p_type_dict', t, len(t))
        # t[0] = DictType(t[3], t[5])
        t[0] = createDictType(t[3], t[5])

    def ap_go_type_tuple(self, t):
        # 'go_type : LPAREN go_type_list RPAREN'
        t[0] = TupleType(t[2])

    def ap_go_type_set(self, t):
        # 'go_type : LBRACE go_type RBRACE'
        # print('p_type_dict', t, len(t))
        t[0] = SetType(t[2])

    def p_go_type_interface(self, t):
        'go_type : INTERFACE LBRACE RBRACE'
        # print('p_type_dict', t, len(t))
        t[0] = makePrimitiveType('AnyRef')

    def p_go_type_function(self, t):
        'go_type : FUNC go_func_spec'
        t[0] = t[2]

    def p_go_type_list_1(self, t):
        'go_type_list : go_type'
        t[0] = [t[1]]

    def p_go_type_list_2(self, t):
        'go_type_list : go_type_list COMMA go_type'
        t[0] = t[1] + [t[3]]

    def p_go_id_list(self, t):
        'go_id_list : ID'
        t[0] = [t[1]]

    def p_id_list_2(self, t):
        'go_id_list : go_id_list COMMA ID'
        t[0] = t[1] + [t[3]]


    def p_go_param(self, t):
        'go_param : go_id_list go_type'
        t[0] = [Param(name, t[2]) for name in t[1]]

    def p_go_param_1(self, t):
        'go_param : ID ELLIPSIS go_type'
        t[0] = [Param(t[1], t[3])]

    def p_go_param_3(self, t):
        'go_param : go_type'
        t[0] = [Param('', t[1])]

    def p_go_param_list_1(self, t):
        'go_param_list : go_param'
        t[0] = t[1]

    def p_go_param_list_2(self, t):
        'go_param_list : go_param_list COMMA go_param'
        latestparam = t[3][0]
        if latestparam.name != '' and latestparam.type is not None:
            params = t[1]
            assert len(params) > 0
            for i in range(len(params)):
                pos = len(params) - i - 1
                param = params[pos]
                if param.name == '':
                    assert isinstance(param.type, UserType) and param.type.fullpath == param.type.path[0]
                    param.name = param.type.fullpath
                    param.type = latestparam.type.clone()
                else:
                    break
        t[0] = t[1] + t[3]

    def p_go_params(self, t):
        'go_params : LPAREN go_param_list RPAREN'
        t[0] = t[2]

    def p_go_params_empty(self, t):
        'go_params : LPAREN RPAREN'
        t[0] = []

    def p_go_func_spec(self, t):
        'go_func_spec : go_params go_type'
        t[0] = FuncSpec(t[1], t[2])

    def p_go_func_spec_1(self, t):
        'go_func_spec : go_params'
        t[0] = FuncSpec([], None)

    def p_go_func_spec_2(self, t):
        'go_func_spec : go_params go_params'
        t[0] = FuncSpec(t[1], createTupleType([p.type for p in t[2]]))

    def p_go_func_decl(self, t):
        'go_func_decl : FUNC ID go_func_spec'
        t[0] = FuncProto(t[2], t[3])

    def p_go_func_decl_extend(self, t):
        'go_func_decl : FUNC LPAREN ID TIMES ID RPAREN ID go_func_spec'
        t[0] = FuncProto(t[7], t[8], PointerType(UserType([t[5]])))

    def p_go_func_decl_extend_2(self, t):
        'go_func_decl : FUNC LPAREN ID ID RPAREN ID go_func_spec'
        t[0] = FuncProto(t[6], t[7], UserType([t[4]]))

    def p_go_var_item(self, t):
        'go_var_item : ID EQUALS go_expr'
        # print('p_go_var_item', t[1], t[3])
        t[0] = SingleVarDef(t[1], None, t[3])

    def p_go_var_item_1(self, t):
        'go_var_item : ID go_type'
        t[0] = SingleVarDef(t[1], t[2], None)

    def p_go_var_item_2(self, t):
        'go_var_item : ID go_type EQUALS go_expr'
        # print('p_go_var_item_2', t[1], t[2], t[4])
        t[0] = SingleVarDef(t[1], t[2], t[4])

    def p_go_var_item_list(self, t):
        'go_var_item_list : go_var_item'
        t[0] = [t[1]]

    def p_go_var_item_list_2(self, t):
        'go_var_item_list : go_var_item_list newlines go_var_item'
        t[0] = t[1] + [t[3]]


    def p_go_const_item(self, t):
        'go_const_item : go_var_item'
        t[0] = t[1]

    def p_go_const_item_id(self, t):
        'go_const_item : go_identifier'
        t[0] = SingleVarDef(t[1], None, None)

    def p_go_const_item_list(self, t):
        'go_const_item_list : go_const_item'
        t[0] = [t[1]]

    def p_go_const_item_list_2(self, t):
        'go_const_item_list : go_const_item_list newlines go_const_item'
        t[0] = t[1] + [t[3]]


    def p_go_var_decl(self, t):
        'go_var_decl : VAR go_var_item'
        t[0] = t[2]

    def p_go_var_decl_2(self, t):
        'go_var_decl : VAR LPAREN newlines go_var_item_list newlines RPAREN'
        t[0] = MultipleVarDef(t[4])


    def p_go_const_decl(self, t):
        'go_const_decl : CONST go_var_item'
        t[0] = t[2]

    def p_go_const_decl_2(self, t):
        'go_const_decl : CONST LPAREN newlines go_const_item_list newlines RPAREN'
        t[0] = MultipleVarDef(t[4])


    def p_go_type_def(self, t):
        'go_type_def : TYPE ID go_type'
        assert t[3], ('p_type_def', list(t))
        t[0] = TypeDef(t[2], t[3])


    def p_go_struct(self, t):
        'go_struct : TYPE ID STRUCT LBRACE newlines go_var_item_list newlines RBRACE'
        t[0] = ClassDef([], t[2], [], [], t[6], [], ClassType.normal)

    def p_go_struct_1(self, t):
        'go_struct : TYPE ID STRUCT LBRACE newlines go_bases go_var_item_list newlines RBRACE'
        t[0] = ClassDef([], t[2], [], t[6], t[7], [], ClassType.normal)

    def p_go_struct_empty(self, t):
        'go_struct : TYPE ID STRUCT LBRACE newlines go_bases RBRACE'
        t[0] = ClassDef([], t[2], [], t[6], [], [], ClassType.normal)

    def p_go_bases_0(self, t):
        'go_bases : maybe_newlines'
        t[0] = []

    def p_go_bases_1(self, t):
        'go_bases : go_id_path newlines'
        t[0] = [UserType(t[1])]

    def p_go_bases_2(self, t):
        'go_bases : go_bases go_id_path newlines'
        t[0] = t[1] + [UserType(t[2])]

    def p_go_func_proto_decl(self, t):
        'go_func_proto_decl : ID go_func_spec'
        t[0] = FuncProto(t[1], t[2])

    def p_go_func_proto_decl_list(self, t):
        'go_func_proto_decl_list : go_func_proto_decl'
        t[0] = [t[1]]

    def p_go_func_proto_decl_list_1(self, t):
        'go_func_proto_decl_list : go_func_proto_decl_list newlines go_func_proto_decl'
        t[0] = t[1] + [t[3]]

    def p_go_interface(self, t):
        'go_interface : TYPE ID INTERFACE LBRACE newlines go_bases go_func_proto_decl_list newlines RBRACE'
        t[0] = ClassDef([], t[2], [], t[6], [], t[7], ClassType.interface)

    def p_go_interface_1(self, t):
        'go_interface : TYPE ID INTERFACE LBRACE newlines go_func_proto_decl_list newlines RBRACE'
        t[0] = ClassDef([], t[2], [], [], [], t[6], ClassType.interface)

    def p_go_interface_empty(self, t):
        'go_interface : TYPE ID INTERFACE LBRACE newlines go_bases RBRACE'
        t[0] = ClassDef([], t[2], [], t[6], [], [], ClassType.interface)


    def p_go_decl_list(self, t):
        'go_decl_list : go_decl'
        t[0] = [t[1]]

    def p_go_decl_list_1(self, t):
        'go_decl_list : go_decl_list newlines go_decl'
        t[0] = t[1] + [t[3]]


    def p_go_decl(self, t):
        '''go_decl : go_func_decl
                   | go_var_decl
                   | go_const_decl
                   | go_type_def
                   | go_struct
                   | go_interface
                   '''
        t[0] = t[1]

    def p_newlines_2(self, t):
        '''newlines : newlines NEWLINE '''
        t[0] = []

    def p_newlines(self, t):
        '''newlines : NEWLINE '''
        t[0] = []

    def p_maybe_empty_newliens(self, t):
        'maybe_newlines : newlines'
        # print('p_maybe_empty_newliens', t)
        t[0] = t[1]

    def p_maybe_empty_newliens_1(self, t):
        'maybe_newlines : '
        t[0] = []

    def p_error(self, t):
        #print('p_error', t)
        val = t.value if hasattr(t, 'value') else 't.value'
        lineno = t.lineno if t else ('None', -1)
        print('Parser.p_error Syntax error at "%s" lineno=%s lexpos=%s sourcename=%s' % (val, lineno, t.lexpos if t else -1, self.sourcename))
        traceback.print_stack()
        sys.exit(100)

    def build(self, start):
        if self.lexer is None:
            self.lexer = GoLexer()
        self.lexer.build()
        # optimization may cause problem, setting 'optimize' to False could solve the problem, then restore it to True
        # it seems that sometimes when 'optimize' is setted to True, the cache files are not updated when source files are changed
        self.parser = ply.yacc.yacc(module=self, optimize=False, tabmodule='goparsetab', debugfile='goparser.out', debug=False, start=start, errorlog=LexLogger(sys.stderr))#, debuglog=LexLogger(sys.stderr))
    def __init__(self, lexer=None):
        self.lexer = lexer
        self.parser = None
    def parse(self, s, sourcename=None):
        # print('GoParser.parse', s)
        self.lexer.lexer.lineno = 0
        self.sourcename = sourcename
        return self.parser.parse(s, lexer=self.lexer.lexer, debug=False, tracking=False)

godeclparser = GoParser()
godeclparser.build('go_decl')

if __name__ == '__main__':
    godeclparser.parse(r"const MaxRune='\U0010FFFF'")
    godeclparser.parse(r"const MaxRune='\uFFFD'")
    godeclparser.parse('var Categories = map[string]*RangeTable{\n    "C":  C,\n    "Cc": Cc,\n    "Cf": Cf,\n    "Co": Co,\n    "Cs": Cs,\n    "L":  L,\n    "Ll": Ll,\n    "Lm": Lm,\n    "Lo": Lo,\n    "Lt": Lt,\n    "Lu": Lu,\n    "M":  M,\n    "Mc": Mc,\n    "Me": Me,\n    "Mn": Mn,\n    "N":  N,\n    "Nd": Nd,\n    "Nl": Nl,\n    "No": No,\n    "P":  P,\n    "Pc": Pc,\n    "Pd": Pd,\n    "Pe": Pe,\n    "Pf": Pf,\n    "Pi": Pi,\n    "Po": Po,\n    "Ps": Ps,\n    "S":  S,\n    "Sc": Sc,\n    "Sk": Sk,\n    "Sm": Sm,\n    "So": So,\n    "Z":  Z,\n    "Zl": Zl,\n    "Zp": Zp,\n    "Zs": Zs,\n}')
    godeclparser.parse('var FoldScript = map[string]*RangeTable{}')
    godeclparser.parse('var GraphicRanges = []*RangeTable{\n    L, M, N, P, S, Zs,\n}')
