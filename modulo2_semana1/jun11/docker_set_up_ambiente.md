# Setup do Ambiente

Antes de iniciar os exercícios, configure seu ambiente local seguindo os passos abaixo.

## 1. Atualizar o repositório

Abra um terminal na pasta do projeto e execute:

```bash
git pull
```

---

## 2. Reiniciar o ambiente Docker

Para garantir que todos estejam utilizando a mesma base de dados e configuração, remova os containers e volumes existentes:

```bash
docker compose down -v
```

Em seguida, suba novamente o ambiente:

```bash
docker compose up
```

Mantenha esse terminal aberto enquanto estiver utilizando o banco.

---

## 3. Criar o arquivo `.env`

Se o projeto ainda não possuir um arquivo `.env`, crie um na raiz do projeto.

Adicione sua chave da OpenAI e as configurações do banco:

```env
OPENAI_API_KEY=sua_chave_openai

```

---

## 4. Instalar as dependências

Em um novo terminal, execute:

```bash
pip install -r requirements.txt
```

---

## 5. Configurar o DBeaver

Crie uma nova conexão PostgreSQL utilizando os seguintes parâmetros:

| Campo    | Valor       |
| -------- | ----------- |
| Host     | localhost   |
| Port     | 5450        |
| Database | mydb        |
| User     | postgres    |
| Password | postgres123 |

Após preencher os dados, clique em **Test Connection** para validar a conexão.

---

## 6. Executar o exercício

Após concluir a configuração vá até a pasta modulo2_semana1, excolha o dia da aula, execute:

```bash
python <nome_do_arquivo>.py
```
Para alguns pode ser python3 e não python
---

## Checklist

Antes de começar, confirme:

* [ ] Repositório atualizado (`git pull`)
* [ ] Docker iniciado (`docker compose up`)
* [ ] Arquivo `.env` criado
* [ ] Chave da OpenAI configurada
* [ ] Dependências instaladas
* [ ] DBeaver conectado ao PostgreSQL
* [ ] Exercício executando sem erros
