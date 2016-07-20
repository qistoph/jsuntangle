import traceback
from Parser import AstNode, AstLiteral, AstOp
import logging

log = logging.getLogger("Untangle")

class NoIndent(object):
    def __init__(self, pp):
        self.pp = pp

    def __enter__(self):
        self.org_ind = self.pp.indention
        self.pp.indention = 0

    def __exit__(self, a, b, c):
        self.pp.indention = self.org_ind

class PrettyPrinter(object):
    def __init__(self):
        self.indention = 0

    def toString(self, node):
        if type(node) is list:
            ret = "\n".join(map(self.toString, node))
            return ret
        elif isinstance(node, AstNode):
            printMethod = getattr(self, 'print%s' % type(node).__name__)
            return printMethod(node)
        else:
            raise Exception("Only AstNode's or lists of AstNode's can be printed, not %s" % type(node))

    def indent(self, txt = ""):
        return "%s%s" % ("  " * self.indention, txt)

    def printStatements(self, sts):
        ret = "\n".join(map(self.toString, sts))
        return ret

    def printArguments(self, args):
        ret = "(%s)" % ", ".join(map(self.toString, args))
        return ret

    def printAstComment(self, node):
        ret = "// %s" % node.text
        return ret

    def printAstLiteral(self, node, quote = True):
        ret = ""
        if type(node) is not AstLiteral:
            raise Exception("Can't print AstLiteral %s: %s" % (type(node), node))

        if node.isNull:
            ret = "null"
        elif node.isTrue:
            ret = "true"
        elif node.isFalse:
            ret = "false"
        #elif node.isUndefined:
            #ret = "undefined"
        elif node.isNumber:
            ret = "%g" % node.value
        #elif node.isJsObject:
            ##if node.isJsFunction:
                #ret = 'JS-Function'
            #elif node.isJsArray:
                ##ret = 'JS-array[%u]' % len(node.value)
            #elif node.isJsObject:
                #ret = 'JS-Object'
            #else:
                #ret = '?UNKNOWN?'
        #elif node.isFixedArray:
            #ret = 'FixedArray'
        elif node.isString:
            if quote:
                ret = '"%s"' % node.value
            else:
                ret = '%s' % node.value
        else:
            ret = '<unknown literal %s>' % node.value

        return ret

    def printAstArrayLiteral(self, node):
        ret = "[%s]" % ", ".join(map(self.toString, node.values))
        return ret

    def printAstVariableDeclaration(self, node):
        return self.indent("var %s;" % self.toString(node.proxy)) #printAstLiteral(node.proxy.name, False)

    def printAstFunctionLiteral(self, node):
        print "node.scope.declarations: %s" % type(node.scope.declarations)
        ret = "(function %s(%s) {\n" % (node.name, ", ".join(param.name for param in node.scope.parameters))
        self.indention += 1
        if len(node.scope.declarations) > 0:
            ret += self.toString(node.scope.declarations)
            ret += "\n"
        ret += self.toString(node.body)
        ret += "\n"
        self.indention -= 1
        ret += "})"
        return ret

    def printAstFunctionDeclaration(self, node):
        ret = "%s = %s;" % (self.toString(node.proxy), self.toString(node.body))
        return ret

    def printAstProperty(self, node):
        ret = "%s[%s]" % (self.toString(node.obj), self.toString(node.key))
        return ret

    def printAstBlock(self, node):
        ret = "%s" % self.printStatements(node.statements)
        return ret

    def printAstExpression(self, node):
        ret = self.indent("%s;" % self.toString(node.expression))
        return ret

    def printAstBinaryOperation(self, node):
        # Leaving out brackets, precedense should work without
        ret = "%s %s %s" % (self.toString(node.left), node.op.op, self.toString(node.right))
        return ret

    def printAstCompareOperation(self, node):
        ret = "(%s %s %s)" % (self.toString(node.left), node.op.op, self.toString(node.right))
        return ret

    def printAstCountOperation(self, node):
        ret = "("
        if node.isPrefix:
            ret += node.op.op
        ret += self.toString(node.expression)
        if node.isPostfix:
            ret += node.op.op
        ret += ")"
        return ret

    def printAstCallRuntime(self, node):
        if node.name == "InitializeVarGlobal":
            if len(node.args) >= 3:
                ret = '%s = %s' % (self.printAstLiteral(node.args[0], False), self.toString(node.args[2]))
            else:
                ret = '' #TODO: still leaves a ;
        else:
            ret = '%' + node.name + self.printArguments(node.args)
        return ret
    
    def printAstCall(self, node):
        ret = "%s%s" % (self.toString(node.expression), self.printArguments(node.args))
        return ret

    def printAstCallNew(self, node):
        ret = "new %s%s" % (self.toString(node.expression), self.printArguments(node.args))
        return ret

    def printAstReturnStatement(self, node):
        ret = self.indent("return %s;" % (self.toString(node.expression)))
        return ret

    def printAstAssignment(self, node):
        ret = "%s %s %s" % (self.toString(node.target), self.toString(node.op), self.toString(node.value))
        return ret

    def printAstVariableProxy(self, node):
        ret = "%s" % node.name
        return ret

    def printAstConditional(self, node):
        ret = "%s ? %s : %s" % (self.toString(node.condition), self.toString(node.thenExpr), self.toString(node.elseExpr))
        return ret

    def printAstIfStatement(self, node):
        ret = self.indent("if(%s) {\n" % self.toString(node.condition))
        self.indention += 1
        ret += self.toString(node.thenStatement) + "\n"
        self.indention -= 1
        if node.hasElseStatement:
            ret += self.indent("} else {\n")
            self.indention += 1
            ret += self.toString(node.elseStatement) + "\n"
            self.indention -= 1
        ret += self.indent("}")
        return ret

    def printAstForStatement(self, node):
        ret = self.indent("for(")
        if node.init != None:
            with NoIndent(self):
                ret += self.toString(node.init)
                ret += " "
        else:
            ret += "; "
        if node.condition != None:
            ret += self.toString(node.condition)
        ret += "; "
        if node.nextStmt != None:
            with NoIndent(self):
                ret += self.toString(node.nextStmt)
        ret += ") {\n"
        self.indention+=1
        ret += self.toString(node.body) + "\n"
        self.indention-=1
        ret += self.indent("}")
        return ret

    def printAstWhileStatement(self, node):
        ret = self.indent("while(%s) {\n" % self.toString(node.condition))
        self.indention+=1
        ret += self.toString(node.body) + "\n"
        self.indention-=1
        ret += self.indent("}")
        return ret

    def printAstDoWhileStatement(self, node):
        ret = self.indent("do {\n")
        self.indention+=1
        ret += self.toString(node.body) + "\n"
        self.indention-=1
        ret += self.indent("} while(%s);\n" % self.toString(node.condition))
        return ret

    def printAstEmptyStatement(self, node):
        return self.indent(";")

    def printAstOp(self, op):
        if op == AstOp.INIT_VAR:
            return '='
        
        return op.op

    def printAstTODO(self, op):
        log.warning("Printing AstTODO")
        return op.text
