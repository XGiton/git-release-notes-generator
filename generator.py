#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    generator.py
    ~~~~~~~~~~~~~~~~~~~~~~~

    Description of this file

    :author: Zhidong
    :copyright: (c) 2016, Tungee
    :date created: 2016-12-12
    :python version: 2.7

"""
import re
from subprocess import Popen, PIPE, STDOUT


class Commit(object):
    author_name = None  # 作者名字
    author_email = None  # 作者email
    commit_date = None  # 提交时间
    commit_week = None  # 提交的星期
    c_type = None  # 类型
    scope = None  # 范围
    subject = None  # 标题
    body_lines = None  # 正文
    breaking_changes = None  # 大的改变
    testing_points = None  # 测试点

    def __init__(self, commit_entity):
        self.parse(commit_entity)

    def parse(self, commit_entity):
        """解析commit"""
        match = re.match(
            (
                'author_name:(.*)'
                'author_email:(.*)'
                'commit_date:(.*)'
                'subject:(.*)'
                'body:(.*)'
            ),
            commit_entity,
            re.S
        )
        if not match:
            print commit_entity
            return
        author_name, author_email, commit_date, subject, body = [
            _.strip() for _ in match.groups()
            ]
        self.author_name = author_name
        self.author_email = author_email
        self.commit_date, self.commit_week = \
            self.__parse_commit_date(commit_date)
        self.c_type, self.scope, self.subject = \
            self.__parse_subject(subject)
        self.body_lines, self.breaking_changes, self.testing_points = \
            self.__parse_body(body)

    @staticmethod
    def __parse_commit_date(commit_date_str):
        match = re.match(
            '(\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}) (.+)',
            commit_date_str
        )
        commit_date, commit_week = [_.strip() for _ in match.groups()]

        return commit_date, commit_week

    @staticmethod
    def __parse_subject(subject_str):
        match_1 = re.match(
            '(feat|fix|docs|style|refactor|test|chore)(\(.+\)):(.*)',
            subject_str)
        match_2 = re.match(
            '(feat|fix|docs|style|refactor|test|chore):(.*)',
            subject_str)
        c_type = None
        scope = None
        if match_1:
            c_type, scope, subject = match_1.groups()
        elif match_2:
            c_type, subject = match_2.groups()
        else:
            subject = subject_str
        if c_type is not None:
            c_type = c_type.strip()
        if scope is not None:
            scope = scope.strip()
        if subject is not None:
            subject = subject.strip()

        return c_type, scope, subject

    @staticmethod
    def __parse_body(body_str):
        """解析body"""
        body_str = body_str.strip()
        lines = [_ for _ in body_str.split('\n')] if body_str else []
        breaking_index = None
        testing_index = None
        for index, line in enumerate(lines):
            if 'BREAKING CHANGES' in line:
                breaking_index = index
            if 'TESTING POINTS' in line:
                testing_index = index
        # 找出最小的index, 0~index的为body
        breaking_lines = []
        testing_lines = []
        if breaking_index is not None and testing_index is not None:
            if breaking_index > testing_index:
                body_lines = lines[:testing_index]
                testing_lines = lines[testing_index + 1:breaking_index]
                breaking_lines = lines[breaking_index + 1:]
            else:
                body_lines = lines[0:breaking_index]
                breaking_lines = lines[breaking_index + 1:testing_index]
                testing_lines = lines[testing_index + 1:]
        elif breaking_index is not None:
            body_lines = lines[:breaking_index]
            breaking_lines = lines[breaking_index + 1:]
        elif testing_index is not None:
            body_lines = lines[:testing_index]
            testing_lines = lines[testing_index + 1:]
        else:
            body_lines = lines

        return body_lines, breaking_lines, testing_lines


class Log(object):
    commits = []  # commit列表
    new_commits = []
    fix_commits = []
    testing_commits = []

    def __init__(self, since, until):
        log_entity, stderr = self.git_log(since, until)
        self.parse(log_entity)

    def parse(self, log_entity):
        commit_entities = [
            _.strip() for _ in log_entity.split('SPLIT_LINE') if _.strip()
            ]
        for commit_entity in commit_entities:
            commit = Commit(commit_entity)
            self.commits.append(commit)

        return

    @staticmethod
    def git_log(since, until):
        git_command = (
            'git log {since}..{until} '  # 指定commit范围
            '--no-merges '  # 过滤合并的commit
            '-i --pretty=format:"'  # 指定输出格式
            'author_name: %an%n'  # 作者名
            'author_email: %ae%n'  # 作者email
            'commit_date: %cd%n'  # 提交日期
            'subject: %s%n'  # commit标题
            'body: %n%b%n'  # commit正文
            'SPLIT_LINE"'  # 分割线
            ' --date=format:"%Y-%m-%d %H:%M %A"'  # 输出时间格式
        ).format(
            since=since,
            until=until
        )
        p = Popen(
            git_command, shell=True, stdin=PIPE,
            stdout=PIPE, stderr=PIPE, close_fds=True,
            env=None, universal_newlines=False)

        stdout, stderr = p.communicate()

        return stdout, stderr

    def generate_release_notes(self):
        self.commits.sort(key=lambda x: x.commit_date)
        for commit in self.commits:
            if commit.c_type == 'feat':
                self.new_commits.append(commit)
            elif commit.c_type == 'fix':
                self.fix_commits.append(commit)
            if commit.testing_points:
                self.testing_commits.append(commit)

        contexts = []
        f = open('changelog.md', 'w')
        if self.new_commits:
            contexts.append(u'### New Features')
            for commit in self.new_commits:
                note = self.generate_commit_release_note(commit)
                contexts.append('\n'.join(note))
                contexts.append('')
            contexts.append('')
        if self.fix_commits:
            contexts.append(u'### Fixed')
            for commit in self.fix_commits:
                note = self.generate_commit_release_note(commit)
                contexts.append('\n'.join(note))
                contexts.append('')
            contexts.append('')
        if self.testing_commits:
            contexts.append(u'### Testing Points')
            for commit in self.testing_commits:
                note = self.generate_commit_release_note(commit)
                contexts.append('\n'.join(note))
                contexts.append('')
            contexts.append('')

        commit_str = '\n'.join([str(_) for _ in contexts])
        f.write(commit_str)
        f.close()

    @staticmethod
    def generate_commit_release_note(commit):
        author_format = (
            '  [{author_name}]({author_email}) - '
            '{commit_date} {commit_week}'
        )
        body_format = (
            '  {body}'
        )
        breaking_format = (
            '    {breaking_changes}'
        )
        testing_format = (
            '  {testing_points}'
        )
        note = list()
        note.append('* __%s__' % commit.subject)
        note.append('')
        author_line = author_format.format(
            author_name=commit.author_name,
            author_email=commit.author_email,
            commit_date=commit.commit_date,
            commit_week=commit.commit_week
        )
        note.append(author_line)
        note.append('')
        if commit.body_lines:
            body_line = body_format.format(
                body='\n  '.join(commit.body_lines)
            )
            note.append(body_line)
            note.append('')
        if commit.breaking_changes:
            note.append('  **BREAKING CHANGES:**')
            breaking_line = breaking_format.format(
                breaking_changes='\n    '.join(commit.breaking_changes)
            )
            note.append(breaking_line)
            note.append('')
        if commit.testing_points:
            note.append('  **TESTING POINTS:**')
            testing_line = testing_format.format(
                testing_points='\n    '.join(commit.testing_points)
            )
            note.append(testing_line)
            note.append('')

        return note


def main():
    # 获取git log
    since = '0066cf607c93dc00434b0215d455907c9f44c2bb'
    until = 'HEAD'
    log = Log(since, until)
    log.generate_release_notes()


if __name__ == '__main__':
    main()