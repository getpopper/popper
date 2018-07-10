#!/usr/bin/env python

import click
import os
import sys
import popper.utils as pu

from popper.cli import pass_context
from lark import Lark, InlineTransformer, Tree

# This function increments the node_ids for the workflow graph


def increment(node_id):
    """Increments the id of a node during the dot graph
    generation.

    Returns:
        node_id(str): incremented id for the next node
    """
    return 's{}'.format(int(node_id[1:]) + 1)

# This function creates an if-node in the workflow graph


def create_if_node(node_id, c, prev_node):
    """Writes an if node during the dot graph generation
    and returns its node id.

    Args:
        node_id (str): the id of the 'if' node.
        c (str): label for the 'if' node.
        prev_node (str): the id of the parent node.

    Returns:
        A list comprising of :
            node_id (str): node id of the newly created 'if' node,
            True for the successful generation of the 'if' node
    """
    print('{} [shape=oval, label="{}"];'.format(node_id, c))
    print('{} -> {};'.format(prev_node, node_id))
    node_id = increment(node_id)
    return [True, node_id]


""" This function removes the redundant if-else statements
from the comment stack.
"""


def remove_redundant_if(cs):
    for i, item in enumerate(cs):
        if item == '[wf]#if#':
            if cs[i + 1] == '[wf]#fi#':
                cs[i] = ''
                cs[i + 1] = ''
            elif (
                    cs[i + 1] == '[wf]#elif#'or cs[i + 1] == '[wf]#else#'
            ) and cs[i + 2] == '[wf]#fi#':
                cs[i] = ''
                cs[i + 1] = ''
                cs[i + 2] = ''

    new_cs = []
    for item in cs:
        if item != '':
            new_cs.append(item)

    return new_cs


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
                ls += self._pretty(level + 1, n)
            else:
                ls += ['%s' % (n,), ' ']

        return ls

    def pretty(self, tree):
        return ''.join(self._pretty(0, tree))


@click.command('workflow', short_help='Get .dot diagram of a pipeline.')
@click.argument('pipeline', required=False)
@pass_context
def cli(ctx, pipeline):
    """Generates a workflow diagram corresponding to a Popper pipeline, in the
    .dot format. The string defining the graph is printed to stdout so it can
    be piped into other tools. For example, to generate a png file, one can
    make use of the graphviz CLI tools:
    popper workflow mypipe | dot -T png -o mypipe.png
    """
    pipes = pu.read_config()['pipelines']

    if not pipeline:
        get_pipe = pu.in_pipeline(name=True)
        if get_pipe is not None:
            pipeline = get_pipe
        else:
            pu.fail("This is not a pipeline")

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

    cs = transformer.comment_stack
    cs = remove_redundant_if(cs)
    # print(cs)
    print('digraph pipeline {')
    curr_node = None
    prev_node = None
    node_id = 's{}'.format(0)
    curr_if_node = None
    if_created = False
    if_index = None
    for i, item in enumerate(cs):
        if item == '[wf]#stage#':
            prev_item = cs[i - 1]
            next_item = cs[i + 1]
            label = '"{' + '{} | {}'.format(next_item, prev_item) + '}"'
            curr_node = (next_item.replace('-', '_')).replace('.sh', ' ')
            # create the stage node
            print('{} [{}];'.format(
                curr_node,
                'shape=record, label=' + label
            ))

            if prev_node:
                print('{} -> {};'.format(prev_node, curr_node))

            prev_node = curr_node
            continue

        # initialize the if-node
        elif item == '[wf]#if#':
            if_created = False
            c = 'condition'
            if i > 1 and (
                    not cs[i - 1].startswith('[wf]#') and
                    '.sh' not in cs[i - 1]
            ):
                c += ' : {}'.format(cs[i - 1])

            if_index = i - 1
            curr_if_node = node_id

        # inside if-elif-else construct
        elif(
                item == '[wf]#else#' or
                item == '[wf]#elif#' or
                item == '[wf]#fi#'
        ):
            if not cs[i - 1].startswith('[wf]#'):
                if not if_created:
                    if_created, node_id = create_if_node(node_id, c, prev_node)

                print('{} [shape=record, label="{}"];'.format(
                    node_id, cs[i - 1]))
                print('{} -> {};'.format(curr_if_node, node_id))
                node_id = increment(node_id)

                if item == '[wf]#fi':
                    if_created = False

                continue

        # inside loop
        elif item == '[wf]#done':
            c = 'loop'
            if not cs[i - 1].startswith('[wf]#') and '.sh' not in cs[i - 1]:
                c += ' : {}'.format(cs[i - 1])

            print('{} [shape=record,label="{}"];'.format(node_id, c))
            print('{} -> {};'.format(prev_node, node_id))
            node_id = increment(node_id)

        # is a comment outside any control structures
        elif not item.startswith('[wf]#') and '.sh' not in item:

            if i == len(cs) - 1 and not cs[i - 1] == '[wf]#stage#':
                print('{} [shape=record,label="{}"];'.format(node_id, item))
                print('{} -> {};'.format(prev_node, node_id))
                node_id = increment(node_id)
            elif i < len(cs) - 1:
                if (
                        not cs[i + 1].startswith('[wf]#')and
                        not cs[i - 1] == '[wf]#stage#'
                ):
                    print(
                        '{} [shape=record,label="{}"];'.format(
                            node_id, item))
                    print('{} -> {};'.format(prev_node, node_id))
                    node_id = increment(node_id)

    print('}')
