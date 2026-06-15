# Cloud Spark Course Design

云计算技术课程设计项目，目标是在华为云 CCE 上部署容器化 Web 应用，并完成 Spark 大数据分析实验。

## 项目结构

```text
cloud-spark-course-design/
  backend/      # Flask 后端 API
  frontend/     # Nginx 静态前端
  k8s/          # Kubernetes YAML
  spark/        # PySpark 作业与分析脚本
  docs/         # 实验报告、说明文档
```

## 技术栈

- Backend: Python Flask
- Cache/Storage: Redis
- Frontend: HTML + Nginx
- Container: Docker, Docker Compose
- Cloud Native: Kubernetes, Huawei Cloud CCE, SWR, ELB, PVC, HPA
- Data Analysis: PySpark, Pandas

## 第一部分：云计算平台搭建

需要完成：

1. 应用容器化：构建后端和前端镜像，并推送到华为云 SWR。
2. CCE 集群搭建：创建 Kubernetes 集群并配置 `kubectl`。
3. 应用部署：部署 Flask API、Redis、ConfigMap、Secret 和 Service。
4. 持久化存储：为 Redis 配置 PVC，验证 Pod 重建后数据不丢失。
5. ConfigMap Volume 挂载：通过 ConfigMap 挂载 Nginx 配置文件。
6. HPA 弹性伸缩：通过压测验证后端 Pod 自动扩缩容。

## 第二部分：Spark 大数据分析

计划选择 Spark 方向，完成：

1. 部署 Spark Operator。
2. 运行 `wordcount.py` 示例作业。
3. 从 OBS 读取课程数据集。
4. 完成数据清洗、缺失值处理和统计分析。
5. 完成 Pandas 与 PySpark 性能对比，并结合 Amdahl 定律分析。

## 本地运行

代码实现后，可使用 Docker Compose 本地联调：

```bash
docker compose up --build
```

后端健康检查：

```bash
curl http://localhost:5000/api/ping
```

## Kubernetes 部署

配置 CCE 集群的 KubeConfig 后，应用 YAML：

```bash
kubectl apply -f k8s/
kubectl get pods
kubectl get svc
```

## 注意事项

- 不要提交华为云 AK/SK、KubeConfig、SWR 登录信息、Redis 明文密码等敏感信息。
- Secret 文件建议只保留模板，真实密钥通过本地命令或 CI/CD 注入。
- 实验截图建议单独保存，并在最终报告中统一编号。

## 提交材料

- 实验报告 PDF
- GitHub/Gitee 仓库链接
- 邮件主题格式：`【云计算课设】学号_姓名`
