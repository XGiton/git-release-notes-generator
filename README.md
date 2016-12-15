Git 提交信息格式规范

```shell

<type>(<scope>): <subject>

// 空一行

<body>

// 空一行

<footer>

```



### 1. Header

Header 部分只有一行，包括三个字段：type（必需）、scope（可选）和subject（必需）

#### 1-1. type

type 用于说明 commit 的类别，只允许使用下面7个标识：

- feat：新功能（feature）

- fix：修补bug

- docs：文档（documentation）

- style：格式（不影响代码运行的变动）

- refactor：重构（即不是新增功能，也不是修改bug的代码变动）

- test：增加测试

- chore：构建过程或辅助工具的变动（修复正在编写的代码bug也使用该类型）

如果 type 为 feat 和 fix，则该 commit 将肯定出现在 Changelog 之中，其他情况视情况而定



#### 1-2. scope

scope 用于说明 commit 影响的范围，比如数据层、控制层、视图层等等，视项目不同而不同



#### 1-3. subject

subject 是 commit 目的的简短描述，不超过50个字符

- 以动词开头，使用第一人称现在时，比如 change，而不是changed 或 changes

- 第一个字母小写

- 结尾不加句号



### 2. Body

Body 部分是对本次 commit的详细描述，可以分成多行，有两个注意点：

- 使用第一人称现在时，比如使用 change 而不是 changed 或 changes

- 应该说明代码变动的动机，以及与以前行为的对比



### 3. Footer

Footer 部分只用于两种情况

#### 3-1. 不兼容变动

如果当前代码与上一个版本不兼容，则Footer 部分以 BREAKING CHANGES 开头，后面是对变动的描述、以及变动的理由和迁移方法



#### 3-2. 关闭 Issue

如果当前 commit 针对某个 issue，那么可以在 Footer 部分关闭这个 issue

```

Closes #234

```

也可以一次关闭多个 issue

```

Closes #123, #245, #992

```



#### 3-3. 添加测试点

如果 commit 的类型为 feat 或fix，更改的代码需要测试，则需要注明测试点，方便测试的时候根据测试点进行测试，而不会遗漏某个改动没有测试，测试点要保持简洁，描述修改/修复的功能即可

```

TESTING POINTS:

    - 创建模型的流程更改

    - 添加销售线索

```



### 4. Revert

还有一种特殊情况，如果当前 commit 用于撤销以前的commit，则必须以 revert：开头，后面跟着被撤销 commit的Header

```

revert: feat(pencil): add'graphiteWidth' option



This reverts commit 667ecc165

```

Body 部分的格式是固定的，必须写成 This reverts commit <commit_hash>.，其中 hash 是被撤销 commit 的 SHA 标识符