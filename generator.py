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

    author_name = None        # 作者名字
    author_email = None       # 作者email
    commit_date = None        # 提交时间
    commit_week = None        # 提交的星期
    c_type = None             # 类型
    scope = None              # 范围
    subject = None            # 标题
    body = None               # 正文
    breaking_changes = None   # 大的改变
    testing_points = None     # 测试点

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
        self.c_type, self.subject, self.scope = \
            self.__parse_subject(subject)
        self.body, self.breaking_changes, self.testing_points = \
            self.__parse_body(body)

    @staticmethod
    def __parse_commit_date(commit_date_str):
        match = re.match(
            '(\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}) (.{3})',
            commit_date_str
        )
        commit_date, commit_week = [_.strip() for _ in match.groups()]

        return commit_date, commit_week

    @staticmethod
    def __parse_subject(subject_str):
        match_1 = re.match(
            '(feat|fix|docs|style|refactor|test|chore)(\(\.+\)):(.*)',
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
        # body_str = re.sub('^\s*|\s*$', '', body_str)
        body_str = body_str.strip()
        match = re.match(
            '(.*)(BREAKING_CHANGE:.*)?(TESTING_POINT:.*)?',
            body_str,
            re.S)
        body, breaking_change, testing_point = match.groups()
        body = body.strip()
        if breaking_change is not None:
            breaking_change = breaking_change.strip()
            breaking_change = breaking_change.replace(
                'BREAKING CHANGE',
                '**BREAKING CHANGE**'
            )
        if testing_point is not None:
            testing_point = testing_point.strip()
            testing_point = testing_point.replace(
                'TESTING POINT',
                '**TESTING POINT**'
            )

        return body, breaking_change, testing_point


class Log(object):

    commits = []   # commit列表
    new_commits = []
    fix_commits = []

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
            '--no-merges '               # 过滤合并的commit
            '-i --pretty=format:"'       # 指定输出格式
            'author_name: %an%n'         # 作者名
            'author_email: %ae%n'        # 作者email
            'commit_date: %cd%n'         # 提交日期
            'subject: %s%n'              # commit标题
            'body: %n%b%n'               # commit正文
            'SPLIT_LINE"'                # 分割线
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
        for commit in self.commits:
            if commit.c_type == 'feat':
                self.new_commits.append(commit)
            elif commit.c_type == 'fix':
                self.fix_commits.append(commit)

        context = []
        f = open('changelog.md', 'w')
        if self.new_commits:
            context.append(u'### New Features')
            for commit in self.new_commits:
                note = list()
                note.append('* __%s__' % commit.subject)
                note.append('  [%s](%s) - %s %s' % (
                    commit.author_name,
                    commit.author_email,
                    commit.commit_date,
                    commit.commit_week))
                if commit.body:
                    note.append('%s' % commit.body)
                if commit.breaking_changes:
                    note.append('%s' % commit.breaking_changes)
                if commit.testing_points:
                    note.append('%s' % commit.testing_points)

                context.append('\n'.join(note))
                commit_str = '\n'.join(context)
                f.write(commit_str)
        f.close()


def main():
    # 获取git log
    since = '0066cf607c93dc00434b0215d455907c9f44c2bb'
    until = 'HEAD'
    log = Log(since, until)
    log.generate_release_notes()


if __name__ == '__main__':
    main()