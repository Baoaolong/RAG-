# 魔搭创空间部署：3 步

> 仓库里已经准备好了 `app.py`（魔搭要求的 Streamlit 入口）和 `Dockerfile`，两种类型都能用。

## 前提：绑定阿里云账号

魔搭的**创空间**在创建时要求绑定阿里云账号并完成实名认证（免费）。没绑定的话创建页面会卡住。
入口：https://modelscope.cn/docs/studios/docker

## 第 1 步：创建创空间

1. 打开 https://modelscope.cn/studios/create
2. 名称填 `rag-customer-service`（可自定义）
3. **SDK 类型选 Streamlit**（用 `app.py` 直接跑，最省事；选 Docker 也行，端口已配好 7860，但要求阿里云实名认证）
   - ⚠️ 创建时的默认值是 **Gradio**，不手动改的话页面跑不起来（Gradio 会去找 `app.py` 里的 Gradio 接口，找不到就报错）。
   - 建完发现选错了也能救：用 OpenAPI 打一个 `PATCH /openapi/v1/studios/<用户名>/<空间名>/settings`，body 传 `{"sdk_type":"streamlit"}`，然后 `POST .../deploy` 重新部署。
4. 硬件选免费的 CPU 规格
5. 可见性建议先选**私有**，调通了再改公开

## 第 2 步：把代码推上去

创空间创建后会给你一个 git 地址，形如：

```
https://www.modelscope.cn/studios/你的用户名/rag-customer-service.git
```

因为项目已有 git 仓库且分支是 `main`，而魔搭默认分支是 `master`，所以这样推：

```bash
cd "D:\vsCode\python\RAG项目练习"

git remote add modelscope https://www.modelscope.cn/studios/你的用户名/rag-customer-service.git
git push modelscope main:master
```

如果提示需要登录，用户名填魔搭用户名，密码去这里生成访问令牌：https://modelscope.cn/my/myaccesstoken
（令牌要选**「写权限令牌」**，仅读的推不上去。）

### 首次推送会被拒绝，属正常

创空间创建时会自动生成一个初始化提交（只有 `README.md` 和 `.gitattributes`），所以第一次 `push` 会报：

```
! [rejected]  main -> master (fetch first)
error: failed to push some refs
```

而且 `master` 是受保护分支，`push --force` 也会被服务端拒绝（`You are not allowed to force push code to a protected branch`）。正确做法是先把它的初始化提交拉下来合并，再推：

```bash
git fetch modelscope master
git merge modelscope/master --allow-unrelated-histories -X ours -m "合并创空间初始化提交"
git push modelscope main:master
```

`-X ours` 的意思是：两边都有的文件（README、.gitattributes）保留**我们仓库的版本**。

> 也可以不碰 git：直接在创空间页面的「文件」里上传。但 `chroma_db/` 和 `data/` 必须一起上传，否则向量库为空，提问会答不出东西。

## 第 3 步：配置密钥

在创空间页面找到 **设置 → 环境变量（有的界面叫 Secrets / 密钥）**，添加两个：

| 键名 | 值 | 类型 |
| --- | --- | --- |
| `DASHSCOPE_API_KEY` | 你的百炼密钥（`sk-` 开头） | **密钥（Secret）** |
| `ADMIN_PASSWORD` | 知识库管理页的登录密码 | **密钥（Secret）** |

保存后平台会自动重新部署，等日志出现 `Running` 就成功了。

访问地址：`https://modelscope.cn/studios/你的用户名/rag-customer-service`

### 怎么判断「跑起来了但还不能用」

代码里在没有密钥时的表现是：页面直接 `st.error` 提示缺少 `DASHSCOPE_API_KEY` 然后停下。
所以**看到这个报错 = 镜像没问题、只是密钥还没配**，不是构建失败。

也可以用 OpenAPI 远程确认（把 `<令牌>` 换成写权限令牌）：

```powershell
# 状态：status 走到 Running 才算好
curl.exe -H "Authorization: Bearer <令牌>" `
  https://modelscope.cn/openapi/v1/studios/你的用户名/rag-customer-service

# 健康检查：返回 ok 说明 Streamlit 真的在服务
curl.exe -H "Authorization: Bearer <令牌>" `
  https://你的用户名-rag-customer-service.ms.show/_stcore/health
```

> 私有创空间的这些地址都要带 `Authorization` 头，浏览器里直接打开会返回 403，这是正常的。

## 排错

| 现象 | 原因与处理 |
| --- | --- |
| 页面空白 / 一直 Starting | 看**运行日志**：`ModuleNotFoundError` 说明 requirements.txt 缺包；`SyntaxError` 说明代码有问题 |
| 提示 7860 端口被占用 | 只有 Docker 类型会遇到，端口必须是 `0.0.0.0:7860`，本项目已配好 |
| 提问报鉴权错误 | `DASHSCOPE_API_KEY` 没配上，或填成了明文变量而非 Secret |
| 知识库页密码进不去 | `ADMIN_PASSWORD` 没配 |
| 重启后新传的文档没了 | 免费容器磁盘会重置，见下方说明 |

## 三个必须知道的限制

1. **数据重启即失**：容器文件系统在重启/重建后重置。运行期新上传的知识文档和聊天历史不会保留；仓库里自带的 `chroma_db`、`data/` 不受影响。需要持久化要用平台提供的 `/mnt/workspace` 目录或外部数据库。
2. **免费额度有时间限制**：免费 CPU 资源有配额，长期跑建议关注平台说明。
3. **单文件不要超过 100MB**：超过要走 Git LFS；本项目的向量库文件都在几 MB 级别，没问题。

> 上线成功、有人开始用了之后，如果觉得冷启动慢或想要域名，就切到云服务器方案（见仓库根目录 `setup.sh` 与部署手册）。
