
import sys
from lex import *
from ast import *
import ply.yacc
import traceback
import ast

class Parser(object):
    # Parsing rules

    Aprecedence = (
        ('nonassoc', 'AND', 'OR', 'XOR'),
        ('nonassoc', 'EQ', 'NE', 'GE', 'LE', 'GT', 'LT', 'IS', 'IN'),
        ('right', 'NOT'),
        ('left', 'BAND', 'BOR', 'BXOR'),
        ('right', 'BNOT'),
        ('left', 'PLUS', 'MINUS', 'MOD'),
        ('left', 'TIMES', 'DIVIDE'),
        ('right', 'PLUS', 'MINUS'),
    )

    # dictionary of names
    tokens = Lexer.tokens

    def p_code_unit_3(self, t):
        'code_unit : maybe_newlines script_list import_list global_statement_list'
        t[0] = CodeUnit('', 'gml', PackageDef([]), t[2], t[3], t[4])
        assert t[2], list(t)
    def p_code_unit_4(self, t):
        'code_unit : maybe_newlines PACKAGE id_path newlines script_list import_list global_statement_list'
        t[0] = CodeUnit('', 'gml', PackageDef(t[3]), t[5], t[6], t[7])
        #assert(t[5])

    def p_embedded_statement(self, t):
        'embedded_statement : HASH LBRACE embedded_statement_item RBRACE'
        t[0] = t[3]
    def p_embedded_statement_1(self, t):
        'embedded_statement : BACK_QUOTE embedded_statement_item BACK_QUOTE'
        t[0] = t[2]
        # print('p_embedded_statement', list(t))
    def p_embedded_statement_item(self, t):
        '''embedded_statement_item : global_statement
                                   | function_proto
                                   | statement
                                   '''
        t[0] = EmbeddedStatement(t[1])

    def p_embedded_expr(self, t):
        'embedded_expr : HASH LPAREN expr RPAREN'
        t[0] = EmbeddedExpr(t[3])
        # print('p_embedded_expr', list(t))

    def p_embedded_expr_1(self, t):
        'embedded_expr : BACK_QUOTE expr BACK_QUOTE'
        t[0] = EmbeddedExpr(t[2])
        # print('p_embedded_expr', list(t))

    def p_embedded_code(self, t):
        'embedded_code : HASH string_literal'
        t[0] = EmbeddedCode(t[2])
        # print('p_embedded_code', list(t))

    def p_expr_evaluation_0(self, t):
        'expr_evaluation : DOLLAR identifier'
        t[0] = ExprEvaluation(t[2])
        # print('p_expr_evaluation_0', list(t))

    def p_expr_evaluation(self, t):
        'expr_evaluation : DOLLAR LBRACE expr RBRACE'
        t[0] = ExprEvaluation(t[3])
        # print('p_expr_evaluation', list(t))

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

    def p_import_list_0(self, t):
        'import_list : '
        t[0] = []
    def p_import_list_1(self, t):
        'import_list : import_statement'
        t[0] = [t[1]]
    def p_import_list_2(self, t):
        'import_list : import_list import_statement'
        t[0] = t[1] + [t[2]]

    def p_global_statement_list_0(self, t):
        'global_statement_list : '
        t[0] = []
    def p_global_statement_list_1(self, t):
        'global_statement_list : global_statement newlines'
        t[0] = [t[1]]
    def p_global_statement_list_2(self, t):
        'global_statement_list : global_statement_list global_statement newlines'
        t[0] = t[1] + [t[2]]

    def p_global_statement(self, t):
        '''global_statement : function_definition
                            | class_definition
                            | trait_definition
                            | enum_definition
                            | interface_definition
                            | type_def
                            | var_definition
                            | const_def
                            | extension_def
                            '''
        t[0] = t[1]

    def p_extension_def(self, t):
        'extension_def : EXTENSION ID maybe_newlines class_statements'
        t[0] = ExtensionDef(t[2], t[4])

    def Ap_type_specifier(self, t):
        '''type_specifier : CHAR
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
    def p_id_path_1(self, t):
        'id_path : ID'
        t[0] = [t[1]]
    def p_id_path_2(self, t):
        'id_path : id_path PERIOD ID'
        # print('id_path_2', t, list(t))
        t[0] = t[1] + [t[3]]

    def p_ext_id_path_1(self, t):
        'ext_id_path : ext_idstr'
        t[0] = [t[1]]
    def p_ext_id_path_2(self, t):
        'ext_id_path : ext_id_path PERIOD ext_idstr'
        # print('id_path_2', t, list(t))
        t[0] = t[1] + [t[3]]

    def p_type_void(self, t):
        'type : VOID'
        t[0] = makePrimitiveType('void')
    def p_type_eval(self, t):
        'type : expr_evaluation'
        t[0] = t[1]
    def p_type_0(self, t):
        'type : user_type'
        t[0] = t[1]
    def p_user_type_0(self, t):
        'user_type : id_path'
        t[0] = UserType(t[1])

    def p_user_type_template(self, t):
        'user_type : id_path LT id_list GT'
        t[0] = UserType(t[1], [GenericTypeArg(name) for name in t[3]])

    def p_type_array(self, t):
        'type : type LBRACKET RBRACKET'
        # t[0] = ArrayType(t[1], -1)
        assert False, list(t)
        t[0] = createArrayType(t[1], None)

    def p_type_array_len(self, t):
        'type : type LBRACKET number RBRACKET'
        # t[0] = ArrayType(t[1], t[3])
        t[0] = createArrayType(t[1], t[3])

    def p_type_list(self, t):
        'type : LBRACKET type RBRACKET'
        # t[0] = ListType(t[2])
        t[0] = createListType(t[2])

    def p_type_dict(self, t):
        'type : LBRACE type COLON type RBRACE'
        # print('p_type_dict', t, len(t))
        # t[0] = DictType(t[2], t[4])
        t[0] = createDictType(t[2], t[4])

    def p_type_tuple(self, t):
        'type : LPAREN type_list RPAREN'
        # t[0] = TupleType(t[2])
        print('p_type_tuple', t[2])
        t[0] = createTupleType(t[2])

    def p_type_named_tuple(self, t):
        'type : LPAREN named_type_list RPAREN'
        assert False, ('p_type_named_tuple', list(t))

    def p_type_set(self, t):
        'type : LBRACE type RBRACE'
        # print('p_type_dict', t, len(t))
        # t[0] = SetType(t[2])
        t[0] = createSetType(t[2])

    def p_type_function(self, t):
        'type : FUNC function_spec'
        t[0] = t[2]

    def p_command_cases(self, t):
        'command_cases : LBRACE maybe_newlines command_case_list maybe_newlines RBRACE'
        t[0] = CaseBlock(t[3])
    def p_command_case(self, t):
        'command_case : CASE expr COLON maybe_newlines simple_statement_body'
        t[0] = CaseEntryStmt(t[2], t[5])
    def p_command_case_default(self, t):
        'command_case : DEFAULT COLON maybe_newlines simple_statement_body'
        t[0] = CaseEntryStmt(None, t[4])
    def p_command_case_list_1(self, t):
        'command_case_list : command_case'
        t[0] = [t[1]]
    def p_command_case_list(self, t):
        'command_case_list : command_case_list command_case'
        t[0] = t[1] + [t[2]]

    def p_dict_item_transform(self, t):
        'dict_item_transform : expr TRANSFORM expr'
        t[0] = CaseEntryExpr(t[1], t[3])
    def p_command_mapping(self, t):
        'command_mapping : LBRACE maybe_newlines dict_item_transform_list maybe_newlines RBRACE'
        t[0] = CaseBlock(t[3])

    def p_dict_item_transform_list_1(self, t):
        'dict_item_transform_list : dict_item_transform'
        t[0] = [t[1]]
    def p_dict_item_transform_list(self, t):
        'dict_item_transform_list : dict_item_transform_list newlines dict_item_transform'
        t[0] = t[1] + [t[3]]

    def p_command_arg(self, t):
        '''command_arg : expr
                       '''
        t[0] = t[1]
        # print('p_command_arg', t[1])

    def p_command_arg_list_1(self, t):
        'command_arg_list : expr'
        t[0] = [t[1]]
    def p_command_arg_list_many(self, t):
        'command_arg_list : command_arg_list expr'
        t[0] = t[1] + [t[2]]

    def p_arg_list_paren_empty(self, t):
        'arg_list_paren : LPAREN RPAREN'
        # print('p_arg_list_paren_empty', t)
        t[0] = ([], [])
    def p_arg_list_paren(self, t):
        'arg_list_paren : LPAREN expr_list RPAREN'
        # print('p_arg_list_paren', t)
        t[0] = (t[2], [])
    def p_arg_list_paren_all(self, t):
        'arg_list_paren : LPAREN expr_list COMMA named_arg_list RPAREN'
        # print('p_arg_list_paren_all', t, list(t))
        t[0] = (t[2], t[4])
    def p_arg_list_paren_dict(self, t):
        'arg_list_paren : LPAREN named_arg_list RPAREN'
        # print('p_arg_list_paren_dict', t)
        t[0] = ([], t[2])

    def p_named_arg_list_one(self, t):
        'named_arg_list : ext_idstr EQUALS expr'
        t[0] = [NamedExpressionItem(t[1], t[3])]

    def p_named_arg_list_many(self, t):
        'named_arg_list : named_arg_list COMMA ID EQUALS expr'
        t[0] = t[1] + [NamedExpressionItem(t[3], t[5])]

    def p_script_call(self, t):
        'script : ATSIGN ext_id_path arg_list_paren newlines'
        # print('p_script_call', t)
        t[0] = Script(t[2], t[3][0], t[3][1])
        #assert False, (t[2], t[3][0], t[3][1])
    def p_script(self, t):
        'script : ATSIGN ext_id_path newlines'
        # print('p_script', t)
        t[0] = Script(t[2], [], [])
    def p_script_list_empty(self, t):
        'script_list : '
        t[0] = []
    def p_script_list_one(self, t):
        'script_list : script'
        t[0] = [t[1]]
    def p_script_list_many(self, t):
        'script_list : script_list script'
        t[0] = t[1] + [t[2]]

    def p_type_list_1(self, t):
        'type_list : type'
        t[0] = [t[1]]

    def p_type_list_2(self, t):
        'type_list : type_list COMMA type'
        t[0] = t[1] + [t[3]]

    def p_named_type_item(self, t):
        'named_type_item : ext_idstr COLON type'
        t[0] = [NamedTypeItem(t[1], t[3])]

    def p_named_type_list_1(self, t):
        'named_type_list : named_type_item'
        t[0] = [t[1]]

    def p_named_type_list_2(self, t):
        'named_type_list : named_type_list COMMA named_type_item'
        t[0] = t[1] + [t[3]]

    def p_argument_list_paren_empty(self, t):
        'argument_list_paren : LPAREN RPAREN'
        t[0] = []
    def p_argument_list_paren(self, t):
        'argument_list_paren : LPAREN argument_list RPAREN'
        t[0] = t[2]

    def p_argument_2(self, t):
        'argument : ID COLON type'
        t[0] = Param(t[1], t[3])

    def p_argument_type_only(self, t):
        'argument : type'
        t[0] = Param('', t[1])

    def p_argument_list_1(self, t):
        'argument_list : argument'
        t[0] = [t[1]]

    def p_argument_list_2(self, t):
        'argument_list : argument_list COMMA argument'
        t[0] = t[1] + [t[3]]

    def p_function_spec(self, t):
        'function_spec : LPAREN argument_list RPAREN'
        # print('p_function_spec', list(t))
        t[0] = FuncSpec(t[2], None)

    def p_function_spec_2(self, t):
        'function_spec : LPAREN argument_list RPAREN TRANSFORM type'
        # print('p_function_spec_2', list(t))
        t[0] = FuncSpec(t[2], t[5])

    def p_function_spec_3(self, t):
        'function_spec : LPAREN RPAREN'
        # print('p_function_spec_3', list(t))
        t[0] = FuncSpec([], None)

    def p_function_spec_4(self, t):
        'function_spec : LPAREN RPAREN TRANSFORM type'
        # print('p_function_spec_4', list(t))
        t[0] = FuncSpec([], t[4])

    def p_function_proto_decl(self, t):
        'function_proto_decl : ID function_spec'
        t[0] = FuncProto(t[1], t[2])

    def p_function_proto(self, t):
        'function_proto : FUNC ID function_spec'
        t[0] = FuncProto(t[2], t[3])

    def p_function_proto_2(self, t):
        'function_proto : FUNC BNOT ID function_spec'
        t[0] = FuncProto('~' + t[3], t[4])

    def p_statement_block(self, t):
        'statement_block : statement_body'
        t[0] = StatementBlock(t[1])

    def p_statement_list_0(self, t):
        'statement_list : '
        t[0] = []
    def p_statement_list_newlines(self, t):
        'statement_list : statement'
        t[0] = [t[1]]
    def p_statement_list_1(self, t):
        'statement_list : statement newlines'
        t[0] = [t[1]]
    def p_statement_list_2(self, t):
        'statement_list : statement_list statement newlines'
        t[0] = t[1] + [t[2]]

    def p_assignment_operator(self, t):
        '''
        assignment_operator : EQUALS
                            | TIMESEQUAL
                            | DIVEQUAL
                            | MODEQUAL
                            | PLUSEQUAL
                            | MINUSEQUAL
                            | LSHIFTEQUAL
                            | RSHIFTEQUAL
                            | ANDEQUAL
                            | OREQUAL
                            | XOREQUAL
                            '''
        t[0] = t[1]

    def p_assignment_target_list_one(self, t):
        'assignment_target_list : assignment_target'
        t[0] = [t[1]]

    def p_assignment_target_list_many(self, t):
        'assignment_target_list : assignment_target_list COMMA assignment_target'
        t[0] = t[1] + [t[3]]

    def p_assignment_target(self, t):
        '''
        assignment_target : identifier
                          | attribute_ref
                          | subscription
                          | slicing
                          '''
        t[0] = t[1]

    def p_assignment(self, t):
        'assignment : assignment_target_list assignment_operator expr_list'
        t[0] = Assignment(t[1], t[2], t[3])

    def p_return_statement_one(self, t):
        'return_statement : RETURN expr'
        t[0] = Return(t[2])

    def p_return_statement_tuple(self, t):
        'return_statement : RETURN many_expr_list'
        t[0] = Return(TupleLiteral(t[2]))

    def p_return_statement_empty(self, t):
        'return_statement : RETURN'
        t[0] = Return(None)

    def p_statement_body(self, t):
        'statement_body : LBRACE maybe_newlines statement_list maybe_newlines RBRACE'
        t[0] = StatementBody(t[3])

    def p_simple_statement_body(self, t):
        'simple_statement_body : statement_list'
        t[0] = StatementBody(t[1])

    def p1_if_elseif(self, t):
        'if_elseif : ELSE IF expr statement_body'
        t[0] = IfBranch(t[3], t[4])
    def p_if_elseif2(self, t):
        'if_elseif : ELSEIF expr statement_body'
        t[0] = IfBranch(t[2], t[3])
    def p_if_elseif_list_1(self, t):
        'if_elseif_list : if_elseif'
        t[0] = [t[1]]
    def p_if_elseif_list_2(self, t):
        'if_elseif_list : if_elseif_list if_elseif'
        t[0] = t[1] + [t[2]]

    def p_if_else_statement(self, t):
        'if_statement : IF expr maybe_newlines statement_body ELSE maybe_newlines statement_block'
        # print('p_if_else_statement', list(t))
        t[0] = IfStatement([IfBranch(t[2], t[4])], t[7])

    def p_if_statement(self, t):
        'if_statement : IF expr maybe_newlines statement_body'
        # print('p_if_statement', list(t))
        t[0] = IfStatement([IfBranch(t[2], t[4])], None)

    def p_if_elseif_statement(self, t):
        'if_statement : IF expr maybe_newlines statement_body if_elseif_list'
        # print('p_if_elseif_statement', list(t))
        t[0] = IfStatement([IfBranch(t[2], t[4])] + t[5], None)

    def p_if_elseif_else_statement(self, t):
        'if_statement : IF expr maybe_newlines statement_body if_elseif_list ELSE statement_block'
        # print('p_if_elseif_else_statement', list(t))
        t[0] = IfStatement([IfBranch(t[2], t[4])] + t[5], t[7])

    def p_while_statement(self, t):
        'while_statement : WHILE expr maybe_newlines statement_body'
        t[0] = WhileStatement(t[2], t[4])

    def p_do_while_statement(self, t):
        'do_while_statement : DO maybe_newlines statement_body WHILE expr'
        t[0] = DoWhileStatement(t[5], t[3])

    def p_action_expr(self, t):
        '''action_expr : simple_statement
                       '''
        t[0] = t[1]

    def p_control_expr(self, t):
        '''control_expr : simple_statement
                        | var_definition
                        '''
        t[0] = t[1]

    def p_control_expr_list(self, t):
        'control_expr_list : SEMI'
        t[0] = None
    def p_control_expr_list_2(self, t):
        'control_expr_list : control_expr SEMI'
        t[0] = t[1]

    def p_action_expr_list(self, t):
        'action_expr_list : SEMI'
        t[0] = None
    def p_action_expr_list_2(self, t):
        'action_expr_list : SEMI action_expr'
        t[0] = t[2]

    def p_for_spec_1(self, t):
        'for_spec : control_expr_list action_expr_list'
        t[0] = (t[1], None, t[2])
    def p_for_spec_2(self, t):
        'for_spec : control_expr_list expr action_expr_list'
        t[0] = (t[1], t[2], t[3])

    def p_for_statement(self, t):
        'for_statement : FOR for_spec statement_body'
        # print('p_for_statement')
        t[0] = ForStatement(t[2][0], t[2][1], t[2][2], t[3])

    def p_foreach_seq_statement(self, t):
        'foreach_statement : FOR ID IN expr statement_body'
        # print('p_foreach_seq_statement')
        t[0] = ForEachStatement(SingleVarDef(t[2], None, None), t[4], t[5])

    def p_foreach_dict_statement(self, t):
        'foreach_statement : FOR ID COMMA ID IN expr statement_body'
        # print('p_foreach_dict_statement')
        # t[0] = ForEachStatement(createTupleVarDef(t[2], None, None), t[4], t[5])
        t[0] = ForEachDictStatement(SingleVarDef(t[2], None, None), SingleVarDef(t[4], None, None), t[6], t[7])

    def p_using_statement(self, t):
        'using_statement : USING var_def_item statement_body'
        t[0] = UsingStatement(t[2], t[3])

    def p_break_statement(self, t):
        'break_statement : BREAK'
        t[0] = Break()

    def p_continue_statement(self, t):
        'continue_statement : CONTINUE'
        t[0] = Continue()

    def p_call_statement(self, t):
        'call_statement : call'
        t[0] = CallStatement(t[1])
        # print('p_call_statement', t[1])

    def p_command_call_statement(self, t):
        # 'command_call_statement : identifier command_arg_list'
        'command_call_statement : command_call'
        t[0] = CallStatement(t[1])
        # print('p_command_call_statement', t[1])

    def p_command_statement(self, t):
        'command_statement : DO identifier expr_list'
        callinfo = Call(t[2], t[3])
        t[0] = CallStatement(callinfo)
        # print('p_command_statement', t[1])

    def p_simple_statement(self, t):
        '''simple_statement : call_statement
                            | assignment
                            | command_call_statement
                            | command_statement
                            '''
        t[0] = t[1]
        # print('p_simple_statement', t[1])
    def p_definition_statement(self, t):
        '''definition_statement : type_def
                                | const_def
                                | var_definition
                                '''
        t[0] = t[1]
    def p_control_statement(self, t):
        '''control_statement : return_statement
                             | break_statement
                             | continue_statement
                             '''
        t[0] = t[1]

    def p_compound_statement(self, t):
        '''compound_statement : if_statement
                              | while_statement
                              | do_while_statement
                              | for_statement
                              | foreach_statement
                              | using_statement
                              | statement_block
                              '''
        t[0] = t[1]

    def p_statement(self, t):
        '''statement : simple_statement
                     | definition_statement
                     | control_statement
                     | compound_statement
                     '''
        t[0] = t[1]
        # print('p_statement', t[1])

    def p_type_def(self, t):
        'type_def : TYPEDEF ID EQUALS type'
        assert t[4], ('p_type_def', list(t))
        t[0] = TypeDef(t[2], t[4])

    def p_const_def(self, t):
        'const_def : CONST const_def_item_list'
        t[0] = ConstDef(t[2])

    def p_const_def_item(self, t):
        'const_def_item : ID EQUALS expr'
        t[0] = ConstSpec(t[1], None, t[3])
        # print('ConstSpec', list(t))
    def p_const_def_item_2(self, t):
        'const_def_item : ID COLON type EQUALS expr'
        t[0] = ConstSpec(t[1], t[3], t[5])
        # print('ConstSpec', list(t))

    def p_const_def_item_list_one(self, t):
        'const_def_item_list : const_def_item'
        t[0] = [t[1]]
    def p_const_def_item_list_many(self, t):
        'const_def_item_list : const_def_item_list COMMA const_def_item'
        t[0] = t[1] + [t[3]]

    def p_var_def_item_list_1(self, t):
        'many_var_def_item_list : var_def_item COMMA var_def_item'
        t[0] = [t[1], t[3]]

    def p_var_def_item_list_2(self, t):
        'many_var_def_item_list : many_var_def_item_list COMMA var_def_item'
        t[0] = t[1] + [t[3]]

    def p_var_definition_1(self, t):
        'var_definition : VAR var_def_item'
        t[0] = t[2]
        # print('var_def', list(t), t[0], t[2])
    def p_var_definition_2(self, t):
        'var_definition : VAR many_var_def_item_list'
        t[0] = t[2]
        # print('var_def2', list(t))
        assert False
    def p_var_definition_tuple(self, t):
        'var_definition : VAR many_id_list EQUALS expr'
        t[0] = createTupleVarDef(t[2], None, t[4])

    def p_var_def_item(self, t):
        'var_def_item : ID EQUALS expr'
        t[0] = SingleVarDef(t[1], None, t[3])
        # print('SingleVarDef', list(t))
    def p_var_def_item_2(self, t):
        'var_def_item : ID COLON type EQUALS expr'
        t[0] = SingleVarDef(t[1], t[3], t[5])
        # print('SingleVarDef', list(t))
    def p_var_def_item_3(self, t):
        'var_def_item : ID COLON type'
        t[0] = SingleVarDef(t[1], t[3], None)
        # print('SingleVarDef', list(t))

    def p_command_end_arg(self, t):
        '''command_end_arg : command_cases
                           | command_mapping
                           | closure
                           '''
        t[0] = t[1]

    def p_command_args(self, t):
        'command_args : command_arg_list command_end_arg'
        t[0] = t[1] + [t[2]]

    def p_command_args_2(self, t):
        'command_args : command_end_arg'
        t[0] = [t[1]]

    def p_command_call(self, t):
        'command_call : DO identifier command_args'
        # print('p_call', t, list(t))
        t[0] = Call(t[2], t[3], [])
        # print('p_command_call', t[2], t[3])

    def p_command_call_2(self, t):
        'command_call : DO identifier command_end_arg'
        # print('p_call', t, list(t))
        t[0] = Call(t[2], t[3], [])
        # print('p_command_call', t[2], t[3])


    def p_call_args_empty(self, t):
        'call_args : LPAREN RPAREN'
        # print('p_call_empty', t, list(t))
        t[0] = ([], [])

    def p_call_args_normal(self, t):
        'call_args : LPAREN expr_list RPAREN'
        # print('p_call_normal', t, list(t))
        t[0] = (t[2], [])

    def p_call_args_named(self, t):
        'call_args : LPAREN named_arg_list RPAREN'
        # print('p_call_named', t, list(t))
        t[0] = ([], t[2])

    def p_call_args_full(self, t):
        'call_args : LPAREN expr_list COMMA named_arg_list RPAREN'
        # print('p_call_full', t, list(t))
        t[0] = (t[2], t[4])


    def p_call_normal(self, t):
        'call : primary call_args'
        # print('p_call_empty', t, list(t))
        args, namedArgs = t[2]
        t[0] = Call(t[1], args, namedArgs)

    def p_call_id_generic(self, t):
        'generic_call : TEMPLATE identifier generic_args call_args'
        # print('p_call_empty', t, list(t))
        args, namedArgs = t[4]
        t[0] = Call(GenericExpr(t[2], t[3]), args, namedArgs)

    def p_call_attr_ref_generic(self, t):
        'generic_call : TEMPLATE attribute_ref generic_args call_args'
        # print('p_call_empty', t, list(t))
        args, namedArgs = t[4]
        t[0] = Call(GenericExpr(t[2], t[3]), args, namedArgs)


    def p_multilined_expr_list_1(self, t):
        'multilined_expr_list : expr maybe_newlines COMMA maybe_newlines expr maybe_newlines'
        # print('p_expr_list_1', list(t))
        t[0] = [t[1], t[5]]

    def p_multilined_expr_list_2(self, t):
        'multilined_expr_list : multilined_expr_list COMMA maybe_newlines expr maybe_newlines'
        # print('p_expr_list_2', list(t))
        t[0] = t[1] + [t[4]]
    def p_multilined_many_expr_list_1(self, t):
        'many_multilined_expr_list : multilined_expr_list COMMA maybe_newlines expr maybe_newlines'
        # print('p_many_expr_list_1', list(t))
        t[0] = t[1] + [t[4]]

    def p_expr_list_1(self, t):
        'expr_list : expr'
        # print('p_expr_list_1', list(t))
        t[0] = [t[1]]
    def p_expr_list_2(self, t):
        'expr_list : expr_list COMMA expr'
        # print('p_expr_list_2', list(t))
        t[0] = t[1] + [t[3]]
    def p_many_expr_list_1(self, t):
        'many_expr_list : expr_list COMMA expr'
        # print('p_many_expr_list_1', list(t))
        t[0] = t[1] + [t[3]]

    def p_case_entry_value(self, t):
        'case_entry_value : number'
        t[0] = t[1]
    def p_case_entry_value_1(self, t):
        'case_entry_value : CCONST'
        t[0] = CharLiteral(t[1][1:-1])

    def p_case_entry(self, t):
        'case_entry : CASE case_entry_value COLON maybe_newlines simple_statement_body'
        t[0] = CaseEntry(t[2], t[5])
    def p_case_entry_default(self, t):
        'case_entry : DEFAULT COLON maybe_newlines simple_statement_body'
        t[0] = CaseEntry(None, t[4])
    def p_case_entry_list_one(self, t):
        'case_entry_list : case_entry'
        # print('p_case_entry_list_one')
        t[0] = [t[1]]
    def p_case_entry_list_many(self, t):
        'case_entry_list : case_entry_list case_entry'
        # print('p_case_entry_list_many')
        t[0] = t[1] + [t[2]]

    def p_logical_binary_op(self, t):
        '''logical_binary_operator : AND
                                   | OR
                                   | XOR
                                   '''
        t[0] = t[1]
    def p_logical_unary_operator(self, t):
        '''logical_unary_operator : NOT
                                  '''
        t[0] = t[1]
    def p_bitwise_binary_operator(self, t):
        '''bitwise_binary_operator : BAND
                                   | BOR
                                   | BXOR
                                   '''
    def p_bitwise_unary_operator(self, t):
        '''bitwise_unary_operator : BNOT
                                  '''
        t[0] = t[1]
    def p_arithmetic_unary_operator(self, t):
        '''arithmetic_unary_operator : PLUS
                                     | MINUS
                                     '''
        t[0] = t[1]
    def p_additive_operator(self, t):
        '''additive_operator : PLUS
                             | MINUS
                             '''
        t[0] = t[1]
    def p_multiplicative_operator(self, t):
        '''multiplicative_operator : TIMES
                                   | DIVIDE
                                   | MOD
                                   '''
        t[0] = t[1]
    def p_arithmetic_binary_operator(self, t):
        '''arithmetic_binary_operator : multiplicative_operator
                                      | additive_operator
                                      '''
        t[0] = t[1]
    def p_comparison_operator(self, t):
        '''comparison_operator : EQ
                               | NE
                               | GE
                               | LE
                               | LT
                               | GT
                               | IN
                               '''
        t[0] = t[1]
    def p_comparison_operator2(self, t):
        '''comparison_operator : NOT IN
                               '''
        t[0] = t[1] + '-' + t[2]

    def p_binary_operator(self, t):
        '''binary_operator : arithmetic_binary_operator
                           | comparison_operator
                           | logical_binary_operator
                           | bitwise_binary_operator
                           '''
        t[0] = t[1]
    def p_unary_operator(self, t):
        '''unary_operator : arithmetic_unary_operator
                          | logical_unary_operator
                          | bitwise_unary_operator
                          '''
        t[0] = t[1]

    def p_unary_arithmetic_expr(self, t):
        'unary_arithmetic_expr : arithmetic_unary_operator unary_arithmetic_expr'
        t[0] = UnaryOp(t[1], t[2])
    def p_unary_arithmetic_expr_0(self, t):
        'unary_arithmetic_expr : primary'
        t[0] = t[1]

    def p_multiplicative_expr(self, t):
        'multiplicative_expr : multiplicative_expr multiplicative_operator unary_arithmetic_expr'
        t[0] = BinaryOp(t[2], t[1], t[3])
    def p_multiplicative_expr_0(self, t):
        'multiplicative_expr : unary_arithmetic_expr'
        t[0] = t[1]

    def p_additive_expr(self, t):
        'additive_expr : additive_expr additive_operator multiplicative_expr'
        t[0] = BinaryOp(t[2], t[1], t[3])
    def p_additive_expr_0(self, t):
        'additive_expr : multiplicative_expr'
        t[0] = t[1]

    def p_comparison_expr(self, t):
        'comparison_expr : additive_expr comparison_operator additive_expr'
        t[0] = BinaryOp(t[2], t[1], t[3])
    def p_comparison_expr_0(self, t):
        'comparison_expr : additive_expr'
        t[0] = t[1]

    def p_comparison_expr_as(self, t):
        'comparison_expr : additive_expr AS type'
        t[0] = TypeCast(t[1], t[3])
    def p_comparison_expr_is(self, t):
        'comparison_expr : additive_expr IS type'
        t[0] = TypeCheck(t[1], t[3], True)
    def p_comparison_expr_is_not(self, t):
        'comparison_expr : additive_expr IS NOT type'
        t[0] = TypeCheck(t[1], t[4], False)

    def p_unary_logical_expr(self, t):
        'unary_logical_expr : logical_unary_operator unary_logical_expr'
        t[0] = UnaryOp(t[1], t[2])
    def p_unary_logical_expr_0(self, t):
        'unary_logical_expr : comparison_expr'
        t[0] = t[1]

    def p_binary_logical_expr(self, t):
        'binary_logical_expr : binary_logical_expr logical_binary_operator binary_logical_expr'
        t[0] = BinaryOp(t[2], t[1], t[3])
    def p_binary_logical_expr_0(self, t):
        'binary_logical_expr : unary_logical_expr'
        t[0] = t[1]

    def p_if_else_expr(self, t):
        'if_else_expr : binary_logical_expr IF binary_logical_expr ELSE binary_logical_expr'
        t[0] = IfElseExpr(t[3], t[1], t[5])
        # print('p_if_else_expr', list(t))
    def p_if_else_expr_0(self, t):
        'if_else_expr : binary_logical_expr'
        t[0] = t[1]

    def p_simple_expr(self, t):
        # can be used in restricted context, such as list/dist/set comprehension
        '''simple_expr : binary_logical_expr
                       | anonymous_func'''
        t[0] = t[1]

    def p_anonymous_func(self, t):
        'anonymous_func : FUNC function_spec maybe_newlines statement_body'
        t[0] = Closure(t[2], t[4])

    def p_expr(self, t):
        '''expr : anonymous_func
                | if_else_expr
                | command_call
                | generic_call
                '''
        t[0] = t[1]
        # print('p_expr', t[1])

    def p_inner_function_definition(self, t):
        'function_definition : script_list FUNC ID PERIOD ID function_spec maybe_newlines statement_body'
        # print('p_inner_function_definition', list(t))
        assert len(t[8].statements) >= 0
        t[0] = FuncDef(t[1], t[5], t[6], t[8], UserType([t[3]]))

    def p_simple_inner_function_definition(self, t):
        'function_definition : script_list FUNC ID PERIOD ID function_spec EQUALS maybe_newlines expr'
        # print('p_simple_inner_function_definition', list(t), t[9])
        t[0] = FuncDef(t[1], t[5], t[6], StatementBody([Return(t[9])]), UserType([t[3]]))

    def p_simple_inner_function_definition_1(self, t):
        'function_definition : script_list FUNC ID PERIOD ID EQUALS maybe_newlines expr'
        # print('p_simple_inner_function_definition_1', list(t), t[8])
        t[0] = FuncDef(t[1], t[5], FuncSpec([], None), StatementBody([Return(t[8])]), UserType([t[3]]))

    def p_simple_inner_function_definition_2(self, t):
        'function_definition : script_list FUNC ID PERIOD ID TRANSFORM type EQUALS maybe_newlines expr'
        # print('p_simple_inner_function_definition_2', list(t), t[10])
        t[0] = FuncDef(t[1], t[5], FuncSpec([], t[7]), StatementBody([Return(t[10])]), UserType([t[3]]))

    def p_function_definition(self, t):
        'function_definition : script_list FUNC ID function_spec maybe_newlines statement_body'
        # print('p_function_definition', list(t))
        assert len(t[6].statements) >= 0
        t[0] = FuncDef(t[1], t[3], t[4], t[6])

    def p_simple_function_definition(self, t):
        'function_definition : script_list FUNC ID function_spec EQUALS maybe_newlines expr'
        # print('p_simple_function_definition', list(t), t[7])
        t[0] = FuncDef(t[1], t[3], t[4], StatementBody([Return(t[7])]))

    def p_simple_function_definition_1(self, t):
        'function_definition : script_list FUNC ID EQUALS maybe_newlines expr'
        # print('p_simple_function_definition_1', list(t), t[6])
        t[0] = FuncDef(t[1], t[3], FuncSpec([], None), StatementBody([Return(t[6])]))

    def p_simple_function_definition_2(self, t):
        'function_definition : script_list FUNC ID TRANSFORM type EQUALS maybe_newlines expr'
        # print('p_simple_function_definition_2', list(t), t[8])
        t[0] = FuncDef(t[1], t[3], FuncSpec([], t[5]), StatementBody([Return(t[8])]))

    def p_enum_item_1(self, t):
        'enum_item : ext_idstr'
        t[0] = NamedExpressionItem(t[1], None)
    def p_enum_item(self, t):
        'enum_item : ext_idstr EQUALS number'
        t[0] = NamedExpressionItem(t[1], t[3])

    def p_enum_item_list_one(self, t):
        'enum_item_list : enum_item maybe_newlines'
        t[0] = [t[1]]
    def p_enum_item_list_many(self, t):
        'enum_item_list : enum_item_list COMMA maybe_newlines enum_item maybe_newlines'
        t[0] = t[1] + [t[4]]

    def p_enum_definition(self, t):
        'enum_definition : ENUM ID LBRACE newlines enum_item_list RBRACE'
        t[0] = EnumDef(t[2], t[5])

    def p_class_bases_empty(self, t):
        'class_bases : maybe_newlines'
        t[0] = []

    def p_class_bases_one(self, t):
        'class_bases : COLON maybe_newlines class_base_list maybe_newlines'
        t[0] = t[3]

    def p_class_base_list_1(self, t):
        'class_base_list : user_type'
        t[0] = [t[1]]

    def p_class_base_list_2(self, t):
        'class_base_list : class_base_list maybe_newlines COMMA maybe_newlines user_type'
        t[0] = t[1] + [t[5]]

    def p_func_protos(self, t):
        'func_protos : maybe_newlines LBRACE maybe_newlines function_proto_list maybe_newlines RBRACE'
        t[0] = t[4]

    def p_interface_definition(self, t):
        'interface_definition : script_list INTERFACE ID generic_params maybe_newlines class_bases func_protos'
        t[0] = ClassDef(t[1], t[3], t[4], t[6], [], t[7], ClassType.interface)

    def p_trait_definition(self, t):
        'trait_definition : script_list TRAIT ID generic_params maybe_newlines class_bases func_protos'
        t[0] = ClassDef(t[1], t[3], t[4], t[6], [], t[7], ClassType.trait)

    def p_class_definition(self, t):
        # 'class_definition : script_list CLASS ID class_fields COLON maybe_newlines class_base_list maybe_newlines LBRACE maybe_newlines class_statement_list RBRACE'
        # 'class_definition : script_list CLASS ID generic_params class_fields maybe_newlines class_bases maybe_newlines LBRACE maybe_newlines class_statement_list maybe_newlines RBRACE'
        'class_definition : script_list CLASS ID generic_params maybe_newlines class_fields maybe_newlines class_bases class_statements'
        cls = ClassDef(t[1], t[3], t[4], t[8], t[6], t[9], ClassType.normal)
        # print('class_definition', cls)
        t[0] = cls

    def p_class_statement_list_0(self, t):
        'class_statement_list : '
        # print('p_class_statement_list_0', list(t))
        t[0] = []
    def p_class_statement_list_1(self, t):
        'class_statement_list : class_statement'
        # print('p_class_statement_list_1', list(t))
        t[0] = [t[1]]
    def p_class_statement_list_2(self, t):
        'class_statement_list : class_statement_list newlines class_statement'
        t[0] = t[1] + [t[3]]
        # print('p_class_statement_list_2', t[1], t[2])

    def p_function_proto_list_1(self, t):
        'function_proto_list : function_proto'
        t[0] = [t[1]]
    def p_function_proto_list_2(self, t):
        'function_proto_list : function_proto_list newlines function_proto'
        t[0] = t[1] + [t[3]]

    def p_generic_param(self, t):
        'generic_param : type'
        t[0] = GenericLiteralParam(t[1])

    def p_generic_param_list(self, t):
        'generic_param_list : generic_param'
        t[0] = [t[1]]

    def p_generic_param_list_2(self, t):
        'generic_param_list : generic_param_list COMMA generic_param'
        t[0] = t[1] + [t[3]]

    def p_generic_params_none(self, t):
        'generic_params : '
        t[0] = []

    def p_generic_params(self, t):
        'generic_params : LT generic_param_list GT'
        t[0] = t[2]


    def p_generic_arg_type(self, t):
        'generic_arg : type'
        t[0] = GenericTypeArg(t[1])

    def p_generic_arg_literal(self, t):
        'generic_arg : literal'
        t[0] = GenericLiteralArg(t[1])

    def p_generic_arg_list(self, t):
        'generic_arg_list : generic_arg'
        t[0] = [t[1]]

    def p_generic_arg_list_2(self, t):
        'generic_arg_list : generic_arg_list COMMA generic_arg'
        t[0] = t[1] + [t[3]]

    def p_generic_args_empty(self, t):
        'generic_args : LT GT'
        t[0] = []

    def p_generic_args(self, t):
        'generic_args : LT generic_arg_list GT'
        t[0] = t[2]


    def p_class_fields_none(self, t):
        'class_fields : '
        t[0] = []

    def p_class_fields(self, t):
        'class_fields : LPAREN argument_list RPAREN '
        t[0] = t[2]

    def p_maybe_class_statements_none(self, t):
        'maybe_class_statements : '
        t[0] = []

    def p_maybe_class_statements(self, t):
        'maybe_class_statements : class_statements'
        t[0] = t[1]

    def p_class_statements(self, t):
        'class_statements : LBRACE maybe_newlines class_statement_list maybe_newlines RBRACE'
        t[0] = t[3]

    def p_case_class_definition_1(self, t):
        'case_class_definition : script_list CASE ID generic_params class_fields maybe_class_statements'
        t[0] = CaseClassDef(t[1], t[3], t[4], t[5], t[6])

    def p_class_statement(self, t):
        '''class_statement : class_definition
                           | case_class_definition
                           | function_definition
                           | var_definition
                           | const_def
                           | interface_definition
                           | trait_definition
                           | type_def
                           | extension_def
                           '''
        t[0] = t[1]
        # print('class_statement', list(t), t[1])
    def p_statement_import(self, t):
        'import_statement : IMPORT id_path newlines'
        # print('p_statement_import', t[2])
        t[0] = Import(t[2])
    def p_statement_import_list(self, t):
        'import_statement : IMPORT id_path LPAREN id_list RPAREN newlines'
        # print('p_statement_import_list', t[2], t[4])
        t[0] = Import(t[2], t[4])
    def p_id_path_list_one(self, t):
        'id_list : ID'
        t[0] = [t[1]]
    def p_id_path_list_many(self, t):
        'id_list : many_id_list'
        t[0] = t[1]
    def p_id_list_many(self, t):
        'many_id_list : ID COMMA ID'
        t[0] = [t[1], t[3]]
    def p_id_list_many_2(self, t):
        'many_id_list : many_id_list COMMA ID'
        t[0] = t[1] + [t[3]]

    def p_atom_id(self, t):
        'atom : identifier'
        # print('atom:identifier', t[0], t[1])
        t[0] = t[1]

    def p_atom_this(self, t):
        'atom : THIS'
        #print('atom:identifier', t[0], t[1])
        t[0] = This()

    def p_atom_argument_placeholder(self, t):
        'atom : DOLLAR_NUMBER'
        # print('atom:argument_placeholder', t[0], t[1])
        t[0] = ArgumentPlaceholder(t[1])

    def p_atom_literal(self, t):
        'atom : literal'
        #print('atom:literal', t[0], t[1])
        t[0] = t[1]

    def p_atom_closure(self, t):
        'atom : closure'
        # print('atom:closure', t[0], t[1])
        t[0] = t[1]

    def p_closure_simple(self, t):
        'closure : statement_body'
        t[0] = Closure(None, t[1])

    def p_literal_nil(self, t):
        'literal : NIL'
        # print('literal-nil', t[1], type(t[1]), len(t[1]))
        t[0] = Nil()
    def p_string_literal(self, t):
        'string_literal : SCONST'
        # print('p_string_literal', t[1], type(t[1]), len(t[1]))
        text = t[1][1:-1]
        t[0] = StringEvaluation(StringLiteral(text))

    def p_number(self, t):
        'number : ICONST10'
        t[0] = IntLiteral(t[1], int(t[1]))

    def p_number_2(self, t):
        'number : ICONST16'
        s = t[1][2:]
        t[0] = IntLiteral(s, int(s, 16))

    def p_number_3(self, t):
        'number : ICONST8'
        s = t[1][1:]
        t[0] = IntLiteral(s, int(s, 8))

    def p_literal_integer(self, t):
        'literal : number'
        t[0] = t[1]

    def p_literal_float(self, t):
        'literal : FCONST'
        t[0] = FloatLiteral(t[1], float(t[1]))

    def p_literal_char(self, t):
        'literal : CCONST'
        t[0] = CharLiteral(t[1][1:-1])

    def p_literal_list_tuple(self, t):
        '''literal : list_literal
                   | tuple_literal
                   | string_literal
                   | dict_literal
                   '''
                #    | set_literal
        t[0] = t[1]

    def p_list_literal(self, t):
        'list_literal : LBRACKET multilined_expr_list RBRACKET'
        t[0] = ListLiteral(t[2])

    def p_list_literal_1(self, t):
        'list_literal : LBRACKET newlines multilined_expr_list RBRACKET'
        t[0] = ListLiteral(t[3])

    def p_literal_list_2(self, t):
        'list_literal : LBRACKET expr maybe_newlines RBRACKET'
        t[0] = ListLiteral([t[2]])

    def p_literal_list_3(self, t):
        'list_literal : LBRACKET newlines expr maybe_newlines RBRACKET'
        t[0] = ListLiteral([t[3]])

    def p_literal_empty_list(self, t):
        'list_literal : LBRACKET maybe_newlines RBRACKET'
        t[0] = ListLiteral([])

    def p_tuple_literal(self, t):
        'tuple_literal : LPAREN many_expr_list RPAREN'
        t[0] = TupleLiteral(t[2])
        # print('p_tuple_literal', t[2])

    def p_tuple_literal_1(self, t):
        'tuple_literal : LPAREN newlines many_expr_list RPAREN'
        t[0] = TupleLiteral(t[3])
        # print('p_tuple_literal', t[2])

    def p_tuple_literal_2(self, t):
        'tuple_literal : LPAREN expr_list COMMA RPAREN'
        t[0] = TupleLiteral(t[2])
        # print('p_tuple_literal_2', t[2])

    def p_tuple_literal_4(self, t):
        'tuple_literal : LPAREN newlines expr_list COMMA RPAREN'
        t[0] = TupleLiteral(t[3])
        # print('p_tuple_literal_2', t[2])

    def p_dict_item(self, t):
        'dict_item : expr COLON expr'
        t[0] = DictItem(t[1], t[3])

    def p_dict_item_list_1(self, t):
        'dict_item_list : dict_item maybe_newlines'
        t[0] = [t[1]]
        # print('p_dict_item_list_1', list(t))
    def p_dict_item_list_2(self, t):
        'dict_item_list : dict_item_list COMMA maybe_newlines dict_item'
        t[0] = t[1] + [t[4]]
        # print('p_dict_item_list_2', list(t))

    def p_dict_literal(self, t):
        'dict_literal : LBRACE maybe_newlines dict_item_list maybe_newlines RBRACE'
        t[0] = DictLiteral(t[3])

    def p_dict_literal_empty(self, t):
        'dict_literal : LBRACE maybe_newlines RBRACE'
        t[0] = DictLiteral([])

    def p_call_expr(self, t):
        'call_expr : call'
        t[0] = t[1]

    def pconstruct(self, t):
        'call_expr : user_type dict_literal'
        t[0] = ObjectConstruct(t[1], t[2])

    def p_ext_primary(self, t):
        '''ext_primary : primary
                       '''
                    #    | command_cases
        t[0] = t[1]

    def p_paren_expr(self, t):
        'paren_expr : LPAREN expr RPAREN'
        t[0] = t[2]

    def p_primary(self, t):
        '''primary : atom
                   | attribute_ref
                   | call
                   | subscription
                   | slicing
                   | list_comprehension
                   | embedded_code
                   | embedded_statement
                   | embedded_expr
                   | expr_evaluation
                   | command_cases
                   | command_mapping
                   | paren_expr
                   '''
        # print('primary', t, t[1])
        t[0] = t[1]

    def p_list_comp_for(self, t):
        'list_comp_for : FOR ID IN simple_expr'
        t[0] = ListComprehensionFor(SingleVarDef(t[2], None, None), t[4], None)

    def p_list_comp_for_2(self, t):
        'list_comp_for : FOR ID IN simple_expr IF simple_expr'
        t[0] = ListComprehensionFor(SingleVarDef(t[2], None, None), t[4], t[6])

    def p_list_comp_for_list_1(self, t):
        'list_comp_for_list : list_comp_for'
        t[0] = [t[1]]
    def p_list_comp_for_list_2(self, t):
        'list_comp_for_list : list_comp_for_list list_comp_for'
        t[0] = t[1] + [t[2]]

    def p_list_comprehension(self, t):
        'list_comprehension : LBRACKET expr list_comp_for_list RBRACKET'
        t[0] = ListComprehension(t[2], t[3])

    def p_subscription(self, t):
        'subscription : primary LBRACKET expr RBRACKET'
        # print('atom:subscription', t[0], t[1])
        t[0] = Subscript(t[1], t[3])
    def p_slicing_0(self, t):
        'slicing : primary LBRACKET COLON RBRACKET'
        # print('slicing0', t[0], t[1])
        t[0] = Slicing(t[1], None, None, None)
    def p_slicing_1(self, t):
        'slicing : primary LBRACKET expr COLON RBRACKET'
        # print('slicing1', t[0], t[1])
        t[0] = Slicing(t[1], t[3], None, None)
    def p_slicing_2(self, t):
        'slicing : primary LBRACKET COLON expr RBRACKET'
        # print('slicing2', t[0], t[1])
        t[0] = Slicing(t[1], None, t[4], None)
    def p_subscription_3(self, t):
        'slicing : primary LBRACKET expr COLON expr RBRACKET'
        # print('slicing3', t[0], t[1])
        t[0] = Slicing(t[1], t[3], t[5], None)
    def p_attribute_ref(self, t):
        'attribute_ref : primary PERIOD ext_idstr'
        # print('atom:attribute_ref', t[0], t[1], t[2], t[3])
        t[0] = AttrRef(t[1], t[3])
    def p_builtin_primary(self, t):
        '''builtin_primary : CLASS
                           | FUNC
                           '''
        t[0] = UserType([t[1]])
    def p_attribute_ref_3(self, t):
        'attribute_ref : builtin_primary PERIOD ID'
        #print('atom:attribute_ref', t[0], t[1], t[2], t[3])
        t[0] = AttrRef(t[1], t[3])

    def p_identifier(self, t):
        'identifier : ID'
        # print('identifier: ID', t[1])
        t[0] = Identifier(t[1])

    def p_builtin_idstr(self, t):
        '''builtin_idstr : IMPORT
                         | CONTINUE
                         | BREAK
                         | INTERFACE
                         | TRAIT
                         '''
        t[0] = t[1]
    def p_ext_idstr(self, t):
        '''ext_idstr : ID
                     | builtin_idstr
                     '''
        t[0] = t[1]
    def p_ext_identifier(self, t):
        '''ext_identifier : ID
                          | builtin_idstr
                          '''
        t[0] = Identifier(t[1])

    def p_error(self, t):
        #print('p_error', t)
        val = t.value if hasattr(t, 'value') else 't.value'
        lineno = t.lineno if t else ('None', -1)
        print('Parser.p_error Syntax error at "%s" lineno=%s lexpos=%s sourcename=%s' % (val, lineno, t.lexpos if t else -1, self.sourcename))
        traceback.print_stack()
        sys.exit(100)

    def build(self, start='code_unit'):
        if self.lexer is None:
            self.lexer = Lexer()
        self.lexer.build()
        self.parser = ply.yacc.yacc(module=self, optimize=False, tabmodule='gmlparsetab', debugfile='gmlparser.out', debug=True, start=start, errorlog=LexLogger(sys.stderr))#, debuglog=LexLogger(sys.stderr))
    def __init__(self, lexer=None):
        self.lexer = lexer
        self.parser = None
    def parse(self, s, sourcename=None):
        self.lexer.lexer.lineno = 0
        self.sourcename = sourcename
        return self.parser.parse(s, lexer=self.lexer.lexer, debug=False, tracking=True)


codeparser = Parser()
codeparser.build()

exprParser = Parser()
exprParser.build('expr')

funcProtoParser = Parser()
funcProtoParser.build('function_proto_decl')

funcSpecParser = Parser()
funcSpecParser.build('function_spec')

typeParser = Parser()
typeParser.build('type')

varDefParser = Parser()
varDefParser.build('var_def_item')

def parseExpr(s):
    return exprParser.parse(s)

def parseType(s):
    # print('parseType', s)
    return typeParser.parse(s)

def parseVarDef(s):
    # print('parseCVarDef', s)
    return varDefParser.parse(s)

def parseFuncProto(s):
    # print('parseFuncProto', s)
    proto = funcProtoParser.parse(s)
    if proto.spec.returnType is None:
        proto.spec.returnType = ast.makePrimitiveType('void')
    return proto

def parseFuncSpec(s):
    # print('parseFuncSpec', s)
    spec = funcSpecParser.parse(s)
    if spec.returnType is None:
        spec.returnType = ast.makePrimitiveType('void')
    return spec
