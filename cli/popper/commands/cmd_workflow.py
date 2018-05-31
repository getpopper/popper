#!/usr/bin/env python

import click
import os
import popper.utils as pu
import sys

from popper.cli import pass_context
from lark import Lark, InlineTransformer, Tree


bash_grammar = r"""
start: expr*

expr: command
    | comment
    | ifstmt
    | loop
    | envvar

ifstmt: if cond elif* [else] fi
if: "if" -> in_if
fi: "fi" -> out_if

else: else_token expr+
else_token: "else" -> in_else

elif: elif_token cond
elif_token: "elif" -> in_elif

cond: anystring+ [";"] "then" expr+

loop: ("for" |  "while") anystring+ [";"] "do" expr+ done -> in_loop

done: "done" -> out_loop

comment: "#" anystring* NEWLINE -> process_comment

anystring: WORD | DIGIT | okchars

okchars: "+" | "-" | "/" | "[" | "]" | "!" | "$" | "." | "_" | "=" | ":"
       | "`" | "(" | ")" | "," | "|" | "{" | "}" | "&" | ";" | "%" | "'"
       | "<" | ">" | "^" | "@" | "~" | "*" | "\"" | "\\"

command: anystring+ NEWLINE

envvar: LETTER (LETTER|"_"|DIGIT)* "=" anystring+ NEWLINE

singlequotedstring: "'" anystring* "'"

%import common.DIGIT
%import common.ESCAPED_STRING
%import common.LETTER
%import common.NEWLINE
%import common.STRING_INNER
%import common.WORD
%import common.WS

%ignore WS
"""


class ObtainDotGraph(InlineTransformer):
    def __init__(self):
        self.current_stage = ''
        self.comment_stack = []
        self.seen_stages = {}

    def in_if(self, *args):
        self.comment_stack.append('[wf]#if#')

    def in_elif(self, *args):
        self.comment_stack.append('[wf]#elif#')

    def in_else(self, *args):
        self.comment_stack.append('[wf]#else#')

    def out_if(self, *args):
        self.comment_stack.append('[wf]#fi#')

    def in_loop(self, *args):
        self.comment_stack.append('[wf]#loop#')

    def out_loop(self, *args):
        self.comment_stack.append('[wf]#done')

    def process_comment(self, *args):
        comment = ''
        for i in args[0:-1]:
            comment += self.pretty(i)

        if 'wf' not in comment:
            return

        self.comment_stack.append(comment.replace('wf ', ''))

        if self.current_stage not in self.seen_stages:
            self.seen_stages[self.current_stage] = 1
            self.comment_stack.append('[wf]#stage#')
            self.comment_stack.append(self.current_stage)

    def _pretty(self, level, tree):
        if len(tree.children) == 1 and not isinstance(tree.children[0], Tree):
            return ['%s' % (tree.children[0],), ' ']

        ls = ''
        for n in tree.children:
            if isinstance(n, Tree):
                ls += self._pretty(level+1, n)
            else:
                ls += ['%s' % (n,), ' ']

        return ls

    def pretty(self, tree):
        return ''.join(self._pretty(0, tree))


@click.command('workflow', short_help='Get .dot diagram of a pipeline.')
@click.argument('pipeline', required=True)
@pass_context
def cli(ctx, pipeline):
    """Generates a workflow diagram corresponding to a Popper pipeline, in the
    .dot format. The string defining the graph is printed to stdout so it can
    be piped into other tools. For example, to generate a png file, one can
    make use of the graphviz CLI tools:

    popper workflow mypipe | dot -T png -o mypipe.png
    """
    pipes = pu.read_config()['pipelines']

    if pipeline not in pipes:
        pu.fail("Cannot find pipeline {} in .popper.yml".format(pipeline))

    project_root = pu.get_project_root()
    abs_path = os.path.join(project_root, pipes[pipeline]['path'])
    transformer = ObtainDotGraph()
    parser = Lark(bash_grammar, parser='lalr', lexer='contextual',
                  transformer=transformer)
    for stage in pipes[pipeline]['stages']:
        transformer.current_stage = stage
        stage_file = pu.get_filename(abs_path, stage)

        with open(stage_file, 'r') as f:
            s = f.read()
            parser.parse(s)

    print('digraph pipeline {')

    cs = transformer.comment_stack
    node_id = 0
    next_c = ''
    prev_node = None
    curr_stage = None
    prev_stage = None
    curr_if_stmt_node_id = None

    while len(cs) > 0:
        c = cs.pop(0)

        # get next item on the stack, if there's still one
        if len(cs) > 0:
            next_c = cs.pop(0)
        else:
            next_c = None

        # check if we're processing the first element of a stage
        if next_c and next_c == '[wf]#stage#':
            # create stage parent node

            curr_stage = cs.pop(0).replace('-', '').replace('_', '')

            print('s{} [{}"{}{}|{}{}"];'.format(
                curr_stage,
                'shape=record,style=filled,label=',
                '{', curr_stage, c, '}')
            )

            # add edge from previous stage
            if prev_stage:
                print('s{} -> s{};'.format(prev_stage, curr_stage))

            prev_stage = curr_stage
            prev_node = curr_stage
            continue

        # add prefix to label based on who's next
        if str(next_c) == '[wf]#if#':
            c = 'condition: ' + c
            curr_if_stmt_node_id = node_id
        elif str(next_c) == '[wf]#loop#':
            c = 'loop: ' + c

        # create node
        print('s{} [shape=record,label="{}"];'.format(node_id, c))

        # add edge from previous node
        print('s{} -> s{};'.format(prev_node, node_id))

        if len(cs) == 0:
            # if queue is empty, we're done
            break

        # if inside an if stmt, previous node changes to if/elif/else node
        if next_c == '[wf]#elif#' or next_c == '[wf]#else#':
            prev_node = curr_if_stmt_node_id
        else:
            prev_node = node_id

        if not next_c.startswith('[wf]#'):
            # put it back because next one it's a regular comment
            cs.insert(0, next_c)

        node_id += 1

    print('}')
