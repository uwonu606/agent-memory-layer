# 계층에 걸치는 것의 소속을 적는 자리, 적용 순서, 겪은 문제

관계형 DB, Active Directory의 Group Policy, Ansible의 inventory가 계층에 걸치는 것을 다루는 방식을 원 논문과 공식 문서에서 옮긴 조사다. issue #20 "계층에 걸치는 것의 소속을 다른 시스템은 어디에 적고, 쓰는 사람은 어떤 문제를 겪었는가"에 답한다. 세 시스템을 돌려서 확인한 것은 없고, 문서로 갈리지 않은 것은 #확인하지 못한 것에 모았다.

계층의 가지 여럿에 함께 걸리는 것을 이 글에서는 걸치는 것이라고 부른다. 관계형 DB에서는 다대다 관계에 든 행이고, Group Policy에서는 OU 여럿에 link한 GPO이고, Ansible에서는 host 여럿을 묶는 group이다.

## 출처

2026-11-15에 읽었다. 그날 docs.ansible.com의 `latest`는 version 14이고, postgresql.org의 `current`는 version 18이다. PowerShell 문서는 Windows Server 2025의 것이다.

Microsoft Learn의 문서는 요청 header `Accept: text/markdown`으로 markdown 원문을 받았다. Ansible·PostgreSQL·IBM·Microsoft Support 문서와 Microsoft Q&A는 HTML을, 논문과 교재는 PDF를 받아 글자만 뽑아 읽었다. GitHub issue는 GitHub API에서 본문과 댓글을 받았다.

IBM 문서는 쪽 본문을 돌려주는 주소(`www.ibm.com/docs/api/v1/content/`)에서 받았고, 표에는 사람이 여는 주소를 적었다. 요약을 거친 글은 근거로 쓰지 않았다.

큰따옴표 안의 영어는 원문 그대로이고, 원문의 굵은 글씨와 link 표기는 뺐다. 인용 134개가 받은 원문에 있는지 스크립트로 맞춰 보았다.

쓰는 사람이 겪은 문제는 그 사람이 직접 쓴 보고(GitHub issue, Microsoft Q&A)와 Microsoft가 낸 알려진 문제 글에서만 옮겼다. `보관`이라고 적은 Microsoft 문서는 Microsoft가 archived로 표시한 옛 version의 문서이고, 지금 문서에 같은 문장이 없을 때만 썼다.

| 이 글에서 부르는 이름 | 주소 |
|---|---|
| Codd 1970 | https://dl.acm.org/doi/10.1145/362384.362685 (읽은 사본: https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) |
| DSC 부록 E | https://www.db-book.com/db6/appendices-dir/e.pdf |
| IMS logical relationship | https://www.ibm.com/docs/en/ims/15.6.0?topic=functions-creating-logical-relationships |
| IMS relationship types | https://www.ibm.com/docs/en/ims/15.6.0?topic=relationships-logical-relationship-types |
| IMS intersection data | https://www.ibm.com/docs/en/ims/15.6.0?topic=relationships-intersection-data |
| SSMS many-to-many | https://learn.microsoft.com/en-us/ssms/visual-db-tools/map-many-to-many-relationships-visual-database-tools |
| PostgreSQL constraints | https://www.postgresql.org/docs/current/ddl-constraints.html |
| PostgreSQL ORDER BY | https://www.postgresql.org/docs/current/queries-order.html |
| GP overview | https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-overview |
| GP processing | https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-processing |
| GP scope | https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-scope |
| GPMC | https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-management-console |
| gpresult | https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/gpresult |
| New-GPLink | https://learn.microsoft.com/en-us/powershell/module/grouppolicy/new-gplink |
| Set-GPInheritance | https://learn.microsoft.com/en-us/powershell/module/grouppolicy/set-gpinheritance |
| Get-GPInheritance | https://learn.microsoft.com/en-us/powershell/module/grouppolicy/get-gpinheritance |
| Get-GPResultantSetOfPolicy | https://learn.microsoft.com/en-us/powershell/module/grouppolicy/get-gpresultantsetofpolicy |
| MS-GPOL 2.2.2 | https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gpol/08090b22-bc16-49f4-8e10-f27a8fb16d18 |
| MS-GPOL glossary | https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gpol/2f362c13-9a2d-469b-8c4b-7b4045258995 |
| GP troubleshooting | https://learn.microsoft.com/en-us/troubleshoot/windows-server/group-policy/applying-group-policy-troubleshooting-guidance |
| GP planning guide (보관, Windows Server 2008) | https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2008-r2-and-2008/cc754948%28v=ws.10%29 |
| GP unexpected value (보관, Windows Server 2003) | https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2003/cc758377%28v=ws.10%29 |
| GP inheritance issues (보관, Windows 2000) | https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-2000-server/cc978398%28v=technet.10%29 |
| MS16-072 | https://support.microsoft.com/en-us/kb/3163622 |
| Q&A 1048547 | https://learn.microsoft.com/en-us/answers/questions/1048547/default-domain-policy-with-password-policies-can-i |
| inventory | https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html |
| variables | https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_variables.html |
| playbooks | https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_intro.html |
| config | https://docs.ansible.com/projects/ansible/latest/reference_appendices/config.html |
| general precedence | https://docs.ansible.com/projects/ansible/latest/reference_appendices/general_precedence.html |
| special variables | https://docs.ansible.com/projects/ansible/latest/reference_appendices/special_variables.html |
| tips | https://docs.ansible.com/projects/ansible/latest/tips_tricks/ansible_tips_tricks.html |
| FAQ | https://docs.ansible.com/projects/ansible/latest/reference_appendices/faq.html |
| ansible-inventory | https://docs.ansible.com/projects/ansible/latest/cli/ansible-inventory.html |
| ansible #9065 | https://github.com/ansible/ansible/issues/9065 |
| ansible #49602 | https://github.com/ansible/ansible/issues/49602 |
| ansible #41512 | https://github.com/ansible/ansible/issues/41512 |
| ansible #34949 | https://github.com/ansible/ansible/issues/34949 |
| ansible PR #44865 | https://github.com/ansible/ansible/pull/44865 |

DSC 부록 E는 Silberschatz·Korth·Sudarshan의 교재 Database System Concepts 6판의 Appendix E "Hierarchical Model"이다. Codd의 논문이 계층형 DB의 복제를 적지 않아서 이 교재와 IBM의 IMS 문서를 더 읽었다.

## 세 시스템을 나란히

계층과 걸치는 것 두 행은 이 글이 시스템마다 무엇을 계층으로 보았는지를 적은 것이고, 나머지 행의 근거는 아래 절에 있다.

| 물음 | 관계형 DB | Group Policy | Ansible |
|---|---|---|---|
| 계층 | 없다. 견준 계층형 DB에서는 record의 tree | site, domain, OU | `all` group, 부모 group, 자식 group, host |
| 걸치는 것 | 다른 table의 행 여럿과 이어지는 행 | OU 여럿에 link한 GPO | host 여럿을 묶는 group과 그 변수 |
| 소속을 적는 자리 | 따로 둔 곳. 양쪽의 primary key를 담은 junction table의 행 | 계층 쪽. site·domain·OU의 `gPLink` attribute | 따로 둔 곳. inventory source 안의 group 항목 |
| 걸치는 것이 놓이는 자리 | 제 table | domain마다 한곳. link한 OU 안이 아니다 | group 이름을 딴 `group_vars` 파일이나 폴더, 또는 inventory source 안 |
| 적용 순서 | 없다. 행의 순서는 뜻이 없고 정렬은 query가 고른다 | local GPO, site, domain, OU의 차례. 같은 container 안은 link order의 차례 | `all` group, 부모 group, 자식 group, host의 차례. 같은 층은 group 이름의 알파벳 순 |
| 순서를 정하거나 바꾸는 것 | query의 `ORDER BY` | enforced, block inheritance, loopback | `ansible_group_priority`, `VARIABLE_PRECEDENCE` |
| 겹칠 때 이기는 쪽 | 정한 규칙을 찾지 못했다 | 설정마다 마지막에 적용된 GPO | 변수마다 마지막에 merge된 group |
| 문서의 경고 | connection trap, 가리키는 행이 지워질 때의 처리, 결과 순서에 기대지 말 것 | enforced와 block inheritance를 아껴 쓸 것 | 변수는 한곳에 정의할 것 |
| 쓰는 사람이 겪은 문제 | 설계자들이 connection trap에 빠졌다고 Codd가 적었다 | 적용된 정책이 기대와 다르다 | 고르지 않은 group의 변수가 host에 걸린다 |
| 적용된 것을 보는 도구 | 이 조사에서 보지 않았다 | `gpresult` | `ansible-inventory` |

## 관계형 DB

관계형 model은 다대다 관계의 소속을 양쪽 항목 어디에도 적지 않고 셋째 relation의 행으로 적는다. relation은 Codd가 n-tuple의 집합으로 정의한 것이고, 배열로 그리면 행 하나가 tuple 하나다([Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 1.3절).

### 소속을 적는 자리

| 물음 | 문서가 적은 것 | 원문 | 출처 |
|---|---|---|---|
| 다대다 관계를 담는 자리 | 양쪽 table의 primary key 열을 담은 셋째 table이고, 이름이 junction table이다 | "Many-to-many relationships between tables are accommodated in databases by means of junction tables. A junction table contains the primary key columns of the two tables you want to relate." | [SSMS many-to-many](https://learn.microsoft.com/en-us/ssms/visual-db-tools/map-many-to-many-relationships-visual-database-tools) |
| 그 table을 만드는 수단 | foreign key constraint 둘 | "A table can have more than one foreign key constraint. This is used to implement many-to-many relationships between tables." | [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK) |
| Codd의 예 | supplier·part·project를 잇는 relation `supply`. 세 domain의 조합이 primary key이고 각각이 foreign key다 | "In the relation supply of Figure 1, the combination of supplier, part, project is the primary key, while each of these three domains taken separately is a foreign key." | [Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 1.3절 |
| 관계에만 딸린 값 | junction table의 다른 열 | "You can add other columns to this table, just as you can to any other table." | [SSMS many-to-many](https://learn.microsoft.com/en-us/ssms/visual-db-tools/map-many-to-many-relationships-visual-database-tools) |
| 항목과 관계의 구분 | Codd는 foreign key가 어느 relation에나 있을 수 있어서 둘을 가르기 어렵다고 적는다 | "This distinction is difficult to maintain when one may have foreign keys in any relation whatsoever." | [Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 1.3절 |

### 계층형 DB가 다대다 관계를 담는 방식

tree만 쓰는 계층형 DB는 record를 복제해야 다대다 관계를 담는다. 교재가 적은 해법과 IMS가 둔 기능은 둘 다 복제 대신 pointer를 둔다. segment는 IMS 문서가 계층에 놓이는 데이터 단위를 부르는 이름이다([IMS logical relationship](https://www.ibm.com/docs/en/ims/15.6.0?topic=functions-creating-logical-relationships)).

| 물음 | 문서가 적은 것 | 원문 | 출처 |
|---|---|---|---|
| 계층형 model의 모양 | record를 tree의 모음으로 둔다 | "in the hierarchical model, records are organized as collections of trees, rather than as arbitrary graphs" | [DSC 부록 E](https://www.db-book.com/db6/appendices-dir/e.pdf) 첫 쪽 |
| tree에 다대다 관계를 담으면 | record를 복제해야 한다 | "In the case of many-to-many relationships, record replication is necessary to preserve the tree-structure organization of the database." | [DSC 부록 E](https://www.db-book.com/db6/appendices-dir/e.pdf) E.8절 |
| 복제의 문제 | 고칠 때 어긋나고 자리를 더 쓴다 | "Record replication has two major drawbacks: (1) data inconsistency may result when updating takes place and (2) waste of space is unavoidable." | [DSC 부록 E](https://www.db-book.com/db6/appendices-dir/e.pdf) E.8절 |
| 교재가 적은 해법 | 원본 하나를 두고 다른 자리에는 원본을 가리키는 virtual record를 둔다. tree라는 조건을 푼다 | "Instead of replication, we keep a single copy of the physical record, and everywhere else we keep virtual records containing a pointer to that physical record." | [DSC 부록 E](https://www.db-book.com/db6/appendices-dir/e.pdf) E.5절 |
| IMS에서 복제하게 되는 때 | logical relationship을 쓰지 않을 때 | "An alternative to using logical relationships to resolve the different needs of applications is to create separate databases or carry duplicate data in a single database. However, in both cases this creates duplicate data." | [IMS logical relationship](https://www.ibm.com/docs/en/ims/15.6.0?topic=functions-creating-logical-relationships) |
| IMS가 복제를 꺼리는 까닭 | 두 벌을 함께 고쳐야 한다 | "Extra maintenance is required when duplicate data exists because both sets of data must be kept up to date." | [IMS logical relationship](https://www.ibm.com/docs/en/ims/15.6.0?topic=functions-creating-logical-relationships) |
| IMS의 기능 | 두 segment type 사이에 길을 내는 logical relationship | "By establishing a path between two segment types, logical relationships eliminate the need to store duplicate data." | [IMS logical relationship](https://www.ibm.com/docs/en/ims/15.6.0?topic=functions-creating-logical-relationships) |
| IMS가 소속을 적는 자리 | 셋째 segment인 logical child. 한쪽 부모(physical parent) 아래에 놓이고 다른 쪽 부모(logical parent)를 pointer로 가리킨다 | "ORDER is the physical parent of ORDITEM. ORDITEM is the physical child of ORDER and the logical child of ITEM." | [IMS logical relationship](https://www.ibm.com/docs/en/ims/15.6.0?topic=functions-creating-logical-relationships) |
| IMS에서 관계에만 딸린 값 | logical child에 둔다. 이름이 intersection data다 | "Because the logical child segment links the ORDER and ITEM segments together, data that is unique to the relationship between the two segments can be stored in the logical child." | [IMS intersection data](https://www.ibm.com/docs/en/ims/15.6.0?topic=relationships-intersection-data) |

Codd가 tree에 대해 적은 문제는 복제가 아니라 프로그램이 tree의 모양에 매이는 것이다. Codd는 part와 project의 다대다 관계를 tree로 적는 구조 다섯을 들고, 그 가운데 하나를 가정한 프로그램은 "will fail on at least three of the remaining structures"라고 적는다([Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 1.2.3절).

다섯째 구조는 관계를 양쪽과 나란한 셋째 것으로 둔다. 이름이 "Structure 5. Parts, Projects, and Commitment Relationship as Peers"다([Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 1.2.3절).

Codd는 tree에 바탕을 둔 시스템이 담지 못하는 relation도 하나 든다. 원문은 "several existing information systems (chiefly those based on tree-structured files) fail to provide data representations for relations which have two or more identical domains"이고, 예로 든 시스템은 "The present version of IMS/360"이다([Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 1.3절).

### 적용 순서

Codd의 논문에는 걸린 것을 차례로 적용하는 단계가 나오지 않는다. relation은 집합이고, Codd는 "Since relations are sets, all of the usual set operations are applicable to them."이라고 적는다([Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 2.1절).

| 물음 | 문서가 적은 것 | 원문 | 출처 |
|---|---|---|---|
| 행의 순서 | 뜻이 없다 | "The ordering of rows is immaterial." | [Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 1.3절 |
| query 결과의 순서 | 정렬을 고르지 않으면 정해지지 않는다 | "If sorting is not chosen, the rows will be returned in an unspecified order." | [PostgreSQL ORDER BY](https://www.postgresql.org/docs/current/queries-order.html) |
| 순서를 정하는 길 | query가 정렬을 고른다 | "A particular output ordering can only be guaranteed if the sort step is explicitly chosen." | [PostgreSQL ORDER BY](https://www.postgresql.org/docs/current/queries-order.html) |

내가 읽은 Codd의 논문과 PostgreSQL 문서에는 한 항목에 여럿이 걸릴 때 어느 쪽이 이기는지를 정한 규칙이 없다.

[추정] 순서가 필요하면 쓰는 사람이 junction table에 순서를 담은 열을 두고 `ORDER BY`로 골라야 한다(사례: 위 표의 문장 셋).

### 문제

| 문제 | 문서가 적은 것 | 원문 | 출처 |
|---|---|---|---|
| connection trap | 설계자들이 길을 따라가면 관계가 나온다고 잘못 결론 내렸다. Codd가 적은, 사람이 겪은 문제다 | "A lack of understanding of relational composition has led several systems designers into what may be called the connection trap." | [Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 2.1.4절 |
| connection trap의 내용 | supplier에서 part를 거쳐 project로 가는 길을 다 따라가도 그 supplier가 대는 project의 목록이 되지 않는다 | "if all possible paths are followed from a given supplier via the parts he supplies to the projects using those parts, one will obtain a valid set of all projects supplied by that supplier" | [Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 2.1.4절 |
| 겹쳐 적은 것의 어긋남 | relation끼리 겹치면 겹침을 문장으로 적어 두고 점검한다 | "Whenever the named set of relations is redundant in either sense, we shall associate with that set a collection of statements which define all of the redundancies which hold independent of time between the member relations." | [Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 2.3절 |
| 가리키는 행이 지워질 때 | 쓰는 사람이 처리를 골라야 한다 | "The appropriate choice of ON DELETE action depends on what kinds of objects the related tables represent." | [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK) |
| 가리키는 쪽의 index | foreign key를 선언해도 생기지 않는다 | "the declaration of a foreign key constraint does not automatically create an index on the referencing columns" | [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK) |
| 결과의 순서 | 기대면 안 된다 | "The actual order in that case will depend on the scan and join plan types and the order on disk, but it must not be relied on." | [PostgreSQL ORDER BY](https://www.postgresql.org/docs/current/queries-order.html) |
| IMS에서 한쪽 방향의 관계 둘 | 한쪽을 고쳐도 다른 쪽이 따라 고쳐지지 않는다 | "If data in one database is inserted, deleted, or replaced, the corresponding data in the other database is not updated." | [IMS relationship types](https://www.ibm.com/docs/en/ims/15.6.0?topic=relationships-logical-relationship-types) |
| IMS에서 logical child를 양쪽에 두는 방식 | logical child가 두 벌이 된다 | "With physical pairing, the logical child is duplicate data, so there is some increase in storage requirements." | [IMS relationship types](https://www.ibm.com/docs/en/ims/15.6.0?topic=relationships-logical-relationship-types) |

## Group Policy

Group Policy는 GPO를 domain마다 한곳에 두고, 그 GPO가 어느 container에 걸리는지를 container 쪽에 적는다.

GPO는 "a virtual collection of policy settings, security permissions, and scope of management (SOM) that you can apply to users and computers in AD"이고, OU는 "the lowest-level AD container to which you can assign Group Policy settings"다([GP overview](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-overview)).

### 소속을 적는 자리

| 물음 | 문서가 적은 것 | 원문 | 출처 |
|---|---|---|---|
| GPO 하나를 container 여럿에 | link할 수 있다 | "A GPO can be linked to multiple Active Directory containers." | [GPMC](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-management-console#link-a-gpo) |
| GPO가 놓이는 자리 | domain마다 한곳이고, link한 OU 안이 아니다 | "GPOs are stored on a per-domain basis. For example, if you link a GPO to an OU, the GPO isn't stored in that OU." | [GPMC](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-management-console#link-a-gpo) |
| link를 적는 자리 | site·domain·OU가 가진 `gPLink` attribute. 값은 `[distinguishedNameOfGroupPolicyContainer;linkOptions][...][...]` 모양이다 | "Group Policy linking is possible on AD sites, domains, and OUs because each of these objects contains a GPLink attribute." | [GP scope](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-scope#gplink-attribute) |
| link는 어느 쪽의 속성인가 | container의 속성이다 | "The links are a property of the site, domain, or OU; they are not a property of the GPO." | [GP unexpected value](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2003/cc758377%28v=ws.10%29) (보관) |
| link마다 따로 적는 것 | 끔과 enforced. 그 container와의 link에만 걸린다 | "defining the state of the association of the GPO referenced by the GPO DN with this and only this SOM" | [MS-GPOL 2.2.2](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gpol/08090b22-bc16-49f4-8e10-f27a8fb16d18) |
| link의 순서를 적는 자리 | 같은 attribute 안의 차례 | "The order in which GPO paths appear in this attribute specifies the link order for the associated GPOs." | [MS-GPOL 2.2.2](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gpol/08090b22-bc16-49f4-8e10-f27a8fb16d18) |
| block inheritance를 적는 자리 | domain과 OU가 가진 `gPOptions` attribute | "Each domain and OU in AD has a GPOptions attribute, which can be configured to block inheritance." | [GP processing](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-processing#block-inheritance) |
| 사용자에게 바로 link | 할 수 없다 | "You can't link a GPO directly to a user object." | [GP scope](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-scope#linking) |
| GPO 쪽에 적는 것 | 받을 대상을 좁히는 조건. security filtering은 GPO의 permission이다 | "To apply a GPO, both the Read and Apply Group Policy permissions must be granted to the user or computer." | [GP scope](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-scope#gpo-filtering) |
| security group이 계층을 넘는가 | 넘지 않는다. link한 container 안에서만 좁힌다 | "Only members of this group that are within the site, domain, or OU where the GPO is linked receive the GPO; members of the group in other sites, domains, or OUs do not receive the GPO." | [GP planning guide](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2008-r2-and-2008/cc754948%28v=ws.10%29) (보관) |

SOM(scope of management)은 MS-GPOL이 site·domain·OU container를 부르는 이름이다([MS-GPOL glossary](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-gpol/2f362c13-9a2d-469b-8c4b-7b4045258995)).

### 적용 순서

Group Policy는 GPO를 차례로 적용하고, 같은 설정이 겹치면 뒤에 적용한 GPO가 이긴다. GP scope는 "This method resolves conflicts based on the order of application, where the most recently applied GPO takes precedence."라고 적는다([GP scope](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-scope#gpo-conflict-resolution)).

| 물음 | 문서가 적은 것 | 원문 | 출처 |
|---|---|---|---|
| container 사이의 순서 | local GPO, site, domain, OU의 차례다. OU가 겹쳐 있으면 부모 OU가 먼저다 | "In a nested OU structure, GPOs linked to parent OUs are applied first, followed by GPOs linked to the child OUs." | [GP processing](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-processing) |
| 가까운 쪽과 먼 쪽 | 가까운 container가 이긴다 | "The AD container closest to the computer or user overrides Group Policy set in a higher-level AD container." | [GP processing](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-processing) |
| 같은 container 안의 순서 | link order의 숫자가 큰 것부터 처리한다. 숫자가 작은 쪽이 이긴다 | "When Group Policy is processed, GPOs with a higher link order number are processed before GPOs with a lower link order number." | [New-GPLink](https://learn.microsoft.com/en-us/powershell/module/grouppolicy/new-gplink#-order) |
| 새 link의 자리 | 그 container에서 가장 낮은 우선순위 | "By default, the GPO link is added at the lowest precedence with a link order equal to the number of GPO links to the container, plus one." | [New-GPLink](https://learn.microsoft.com/en-us/powershell/module/grouppolicy/new-gplink#-order) |
| enforced가 하는 일 | 아래 container의 GPO가 덮지 못하게 한다 | "That the settings of the GPO always take precedence over conflicting settings in GPOs that are linked to lower-level containers." | [New-GPLink](https://learn.microsoft.com/en-us/powershell/module/grouppolicy/new-gplink#-enforced) |
| block inheritance가 하는 일 | 위 container에 link된 GPO를 물려받지 않게 한다. enforced link는 막지 못한다 | "Blocking inheritance prevents the settings in GPOs that are linked to higher-level sites, domains, or organizational units from being automatically inherited by the specified domain or OU, unless the link for a GPO is enforced." | [Set-GPInheritance](https://learn.microsoft.com/en-us/powershell/module/grouppolicy/set-gpinheritance#description) |
| 둘이 부딪히면 | enforced가 이긴다 | "Enforced is a link property and takes precedence over block policy inheritance, a container property." | [GP processing](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-processing#block-inheritance) |
| 같은 container의 enforced끼리 | 가장 높은 link가 이긴다 | "If multiple GPOs are linked at the same site, domain, or OU and have the enforced option set, the highest GPO link set to enforced takes precedence." | [GP processing](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-processing#enforced-gpos) |
| 다른 층의 enforced끼리 | 먼 쪽이 이긴다. 평소 규칙과 반대다 | "If there are conflicting settings in GPOs that are enforced at two levels of the hierarchy, the setting enforced furthest from the client prevails. This is a reversal of the usual rule, in which the setting from the nearest-linked GPO would prevail." | [GP unexpected value](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2003/cc758377%28v=ws.10%29) (보관) |
| 충돌을 푸는 단위 | GPO가 아니라 설정 하나하나 | "Conflict resolution applies to individual settings, not to entire GPOs." | [GP unexpected value](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2003/cc758377%28v=ws.10%29) (보관) |
| 컴퓨터 설정과 사용자 설정 | 컴퓨터 설정이 이긴다 | "Computer-related policy settings override user-related policy settings." | [GP processing](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-processing) |
| loopback의 merge mode | 컴퓨터의 GPO 목록을 사용자의 GPO 목록 뒤에 붙인다 | "the list of GPOs for the computer is added to the end of the GPOs for the user. As a result, the computer’s GPOs have higher precedence than the user’s GPOs." | [GP processing](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-processing#loopback-processing-mode) |
| loopback의 replace mode | 사용자의 GPO 목록을 쓰지 않는다 | "only the list of GPOs based on the computer object is used" | [GP processing](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-processing#loopback-processing-mode) |

loopback은 컴퓨터에 걸린 GPO의 사용자 설정을 그 컴퓨터에 sign in한 사용자에게 적용하는 설정이다([GP processing](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-processing#loopback-processing-mode)).

### 적용된 것을 보는 도구

| 도구 | 보이는 것 | 원문 | 출처 |
|---|---|---|---|
| `gpresult` | 사용자가 sign in할 때 그 컴퓨터에 적용된 설정의 결과 | "The gpresult command displays the resulting set of policy settings that were enforced on the computer for the specified user when the user signed in." | [gpresult](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/gpresult) |
| `Get-GPResultantSetOfPolicy` | 같은 결과를 파일로 쓴다 | "Gets and writes the RSoP information for a user, a computer, or both to a file." | [Get-GPResultantSetOfPolicy](https://learn.microsoft.com/en-us/powershell/module/grouppolicy/get-gpresultantsetofpolicy) |
| GPMC의 Group Policy Results | GPO끼리 맞물린 결과 | "Group Policy Results. Allows you to view GPO interaction and to troubleshoot Group Policy deployments." | [GPMC](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-management-console) |
| GPMC의 Group Policy Modeling | 적용하기 전에 결과를 흉내 낸다 | "Group Policy Modeling. Allows you to simulate Resultant Set of Policy (RsoP) data for planning Group Policy deployments before implementing them in the production environment." | [GPMC](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-management-console) |
| `Get-GPInheritance` | container 하나에 걸리는 GPO를 우선순위 차례로 낸다 | "The GPOs are listed according to the order of precedence with which they are applied." | [Get-GPInheritance](https://learn.microsoft.com/en-us/powershell/module/grouppolicy/get-gpinheritance#description) |
| operational event log | 적용된 GPO와 거부된 GPO, 거부된 까닭 | "Events in this log include the list of applied GPOs and a list of denied GPOs that includes the reasons for the denials." | [GP troubleshooting](https://learn.microsoft.com/en-us/troubleshoot/windows-server/group-policy/applying-group-policy-troubleshooting-guidance#troubleshooting-checklist) |

gpresult 문서는 이 도구가 있는 까닭을 "Because you can apply overlapping policy settings to any computer or user, the Group Policy feature generates a resulting set of policy settings when the user signs in."이라고 적는다([gpresult](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/gpresult)).

### 문제

문서가 경고하거나 권하는 것은 여섯이다.

| 경고 | 원문 | 출처 |
|---|---|---|
| enforced를 아껴 쓴다 | "This option should be used sparingly. Casual use of this option complicates troubleshooting." | [New-GPLink](https://learn.microsoft.com/en-us/powershell/module/grouppolicy/new-gplink#-enforced) |
| block inheritance를 아껴 쓴다 | "GPO links that are enforced cannot be blocked. This cmdlet should be used sparingly. Casual use of this cmdlet can complicate troubleshooting." | [Set-GPInheritance](https://learn.microsoft.com/en-us/powershell/module/grouppolicy/set-gpinheritance#notes) |
| 그 까닭. 다른 GPO를 맡은 관리자가 설정이 걸리거나 안 걸리는 까닭을 바로 알 수 없다 | "Routine use of these features can make it difficult to troubleshoot policy because it is not immediately clear to administrators of other GPOs why certain policy settings do or do not apply." | [GP planning guide](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2008-r2-and-2008/cc754948%28v=ws.10%29) (보관) |
| OU 구조를 잘 짜면 GPO를 복제하거나 container 여럿에 link할 일이 준다 | "GPOs linked to the higher layers of the OU structure are inherited by default for OUs at the lower layer, reducing the need to duplicate GPOs or to link a GPO to multiple containers." | [GP overview](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-overview#what-is-an-ou) |
| 걸리는 GPO의 수를 줄인다 | "Applying fewer GPOs to a user or computer can reduce startup or logon times and make it easier to troubleshoot the policy structure." | [GP processing](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-processing#optimize-gpo-processing) |
| GPO를 지워도 다른 domain에 건 link는 남는다 | "Be sure to remove links to the GPO in other domains before deleting this GPO from this domain." | [GPMC](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-management-console#unlink-a-gpo-from-a-site-domain-or-ou) |

GP troubleshooting 문서는 첫 문장에서 "When Group Policy settings don't apply as expected, the interactions between settings and the complexity of your topology can make troubleshooting a challenge."라고 적는다([GP troubleshooting](https://learn.microsoft.com/en-us/troubleshoot/windows-server/group-policy/applying-group-policy-troubleshooting-guidance#summary)).

쓰는 사람이 겪은 문제는 셋을 옮긴다.

| 겪은 문제 | 원문 | 출처 |
|---|---|---|
| 적용된 정책이 기대와 다르다. Microsoft는 원인으로 적용 순서, No Override, block inheritance, 꺼진 GPO를 든다 | "A user managed by Group Policy logs on and the Group Policy applied is different from what you expect." | [GP inheritance issues](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-2000-server/cc978398%28v=technet.10%29) (보관) |
| security filtering을 쓴 GPO가 보안 update 뒤에 적용되지 않았다. update 뒤로 Windows가 사용자 정책을 컴퓨터의 계정으로 읽어서, 그 계정이 GPO를 읽을 permission이 없으면 정책이 걸리지 않는다 | "All user Group Policy, including those that have been security filtered on user accounts or security groups, or both, may fail to apply on domain joined computers." | [MS16-072](https://support.microsoft.com/en-us/kb/3163622) |
| OU에 block inheritance를 걸었는데 domain의 password 정책이 그대로 걸렸다. 답은 그 정책이 OU가 아니라 domain 단위로 걸린다고 적는다 | "So I put my user and computer inside an OU where I checked Block Inheritance." "But I continue to receive errors about passwords complexity." | [Q&A 1048547](https://learn.microsoft.com/en-us/answers/questions/1048547/default-domain-policy-with-password-policies-can-i) |

No Override와 enforced는 같은 option이다. GP planning guide는 이 option을 "Enforced (No Override)"라고 적는다([GP planning guide](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2008-r2-and-2008/cc754948%28v=ws.10%29), 보관).

MS16-072 글은 원인을 "This issue may occur if the Group Policy Object is missing the Read permissions for the Authenticated Users group or if you are using security filtering and are missing Read permissions for the domain computers group."이라고 적는다([MS16-072](https://support.microsoft.com/en-us/kb/3163622)).

## Ansible

Ansible은 host가 어느 group에 드는지를 inventory의 group 항목에 적고, group의 변수는 group 이름을 딴 파일이나 폴더에 둔다.

inventory는 "the managed nodes you automate and the variables associated with those hosts"를 정의하는 것이고, host는 그 managed node다([inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html)).

### 소속을 적는 자리

| 물음 | 문서가 적은 것 | 원문 | 출처 |
|---|---|---|---|
| host의 소속 | inventory source 안에서 group 이름 아래에 host를 적는다. INI에서는 `[group]` 제목 아래이고 YAML에서는 group의 `hosts:` 아래다 | "The headings in brackets are group names." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#inventory-basics-formats-hosts-and-groups) |
| host 하나가 group 여럿에 | 들 수 있다 | "You can put a host in more than one group." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#hosts-in-multiple-groups) |
| 여러 번 적힌 host | 같은 것 하나다 | "If you define a host or group more than once under different ‘branches’ or ‘instances’, the host or group remains the same entity." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#grouping-groups-parent-child-group-relationships) |
| group의 group | 부모 group의 항목에 자식을 적는다 | "In YAML format, use the children: entry." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#grouping-groups-parent-child-group-relationships) |
| 자식 group의 host | 부모 group에도 든다 | "Any host that is a member of a child group is automatically a member of the parent group." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#grouping-groups-parent-child-group-relationships) |
| group의 부모 수 | 여럿일 수 있다. 돌아오는 관계는 둘 수 없다 | "A group can have multiple parents and children, but not circular relationships." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#grouping-groups-parent-child-group-relationships) |
| 모든 host가 드는 group | `all` | "The all group contains every host." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#default-groups) |
| group 변수를 폴더로 두는 방식 | group 이름의 폴더를 두면 Ansible이 그 안의 파일을 다 읽는다 | "You can also create directories named after your groups or hosts. Ansible reads all the files in these directories in lexicographical order." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#organizing-host-and-group-variables) |
| `group_vars`를 찾는 자리 | inventory source 옆과 playbook 파일 옆 | "The host_group_vars plugin loads host and group variable files by searching paths relative to the inventory source or the playbook file." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#organizing-host-and-group-variables) |
| host 쪽에서 소속을 읽는 길 | 실행 때 Ansible이 채우는 변수 `group_names` | "List of groups the current host is part of, it always reflects the inventory_hostname and ignores delegation." | [special variables](https://docs.ansible.com/projects/ansible/latest/reference_appendices/special_variables.html) |

group 변수를 두는 자리는 셋이다. inventory source 안의 `vars:`(INI에서는 `[group:vars]`), `group_vars/<group>` 파일, `group_vars/<group>/` 폴더다([inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#assigning-a-variable-to-many-machines-group-variables), [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#organizing-host-and-group-variables)).

문서의 예에서 `group_vars` 파일에는 변수만 있고 host의 소속은 없다.

playbook은 Ansible에 시킬 task를 적어 두는 파일이다. 문서는 "If you need to execute a task with Ansible more than once, you can write a playbook"이라고 적는다([playbooks](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_intro.html)).

### 적용 순서

Ansible은 실행하기 전에 group의 변수를 host 하나하나에 펴서 합친다. 원문은 "Before executing, however, Ansible always flattens variables, including inventory variables, to the host level."이다([inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#assigning-a-variable-to-many-machines-group-variables)).

| 물음 | 문서가 적은 것 | 원문 | 출처 |
|---|---|---|---|
| 층 사이의 순서 | 낮은 쪽부터 `all` group, 부모 group, 자식 group, host다 | "A child group’s variables have higher precedence (they override) than a parent group’s variables." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#how-variables-are-merged) |
| 같은 층의 group끼리 | 이름의 알파벳 순으로 합치고 뒤에 load된 쪽이 이긴다 | "By default, Ansible merges groups at the same parent/child level in alphabetical order. Variables from the last group that Ansible loads overwrite variables from the previous groups." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#how-variables-are-merged) |
| 같은 층의 순서를 바꾸는 값 | group 변수 `ansible_group_priority`. 기본값은 1이다 | "The larger the number, the later Ansible merges the group, giving it higher priority. This variable defaults to 1 if you do not set it." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#how-variables-are-merged) |
| 그 값을 두는 자리 | inventory source에만 둘 수 있다 | "You can set ansible_group_priority only in an inventory source, not in group_vars/." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#how-variables-are-merged) |
| 겹친 값 | 합치지 않고 덮어쓴다 | "By default, Ansible overwrites variables, including the ones that you define for a group or host" | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#how-variables-are-merged) |
| group이 실행 때까지 남는가 | 남지 않는다 | "so groups do not survive outside of inventory and host matching" | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#how-variables-are-merged) |
| 변수 전체의 우선순위 | 22단계다. group 변수는 3~7번째이고 host 변수가 그 위다 | "Here is the order of precedence from least to greatest (the last listed variables override all other variables)" | [variables](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence) |
| inventory source가 여럿일 때 | 명령에 넘긴 차례로 합친다 | "When you pass multiple inventory sources at the command line, Ansible merges variables in the order you pass those parameters." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#managing-inventory-variable-load-order) |
| 폴더에 inventory source 여럿 | 파일 이름의 알파벳 순으로 합친다 | "When you put multiple inventory sources in a directory, Ansible merges the sources in alphabetical order according to their filenames." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#managing-inventory-variable-load-order) |
| playbook 옆과 inventory 옆의 `group_vars` | playbook 옆이 이긴다 | "the variables that Ansible sources relative to the playbook override the variables that it sources relative to the inventory source" | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#organizing-host-and-group-variables) |
| group 변수의 순서를 바꾸는 설정 | `VARIABLE_PRECEDENCE` | "Allows to change the group variable precedence merge order." | [config](https://docs.ansible.com/projects/ansible/latest/reference_appendices/config.html#variable-precedence) |

22단계 가운데 group 변수가 드는 다섯은 낮은 쪽부터 "Inventory file or script group vars", "Inventory group_vars/all", "Playbook group_vars/all", "Inventory group_vars/*", "Playbook group_vars/*"다([variables](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence)).

[추정] 이 차례를 그대로 읽으면 inventory 파일 안에서 어떤 group에 준 변수는 `group_vars/all` 파일의 변수에 덮인다(사례: 위 다섯 단계의 차례 1개).

### 적용된 것을 보는 도구

`ansible-inventory`는 Ansible이 합친 뒤의 inventory를 보여 준다. 문서는 이 명령을 "used to display or dump the configured inventory as Ansible sees it"이라고 적는다([ansible-inventory](https://docs.ansible.com/projects/ansible/latest/cli/ansible-inventory.html)).

| option | 원문 | 출처 |
|---|---|---|
| `--host <HOST>` | "Output specific host info, works as inventory script. It will ignore limit" | [ansible-inventory](https://docs.ansible.com/projects/ansible/latest/cli/ansible-inventory.html#common-options) |
| `--graph` | "create inventory graph, if supplying pattern it must be a valid group name. It will ignore limit" | [ansible-inventory](https://docs.ansible.com/projects/ansible/latest/cli/ansible-inventory.html#common-options) |
| `--list --yaml` | "By running the following command, you can see inventory variables for a host:" | [FAQ](https://docs.ansible.com/projects/ansible/latest/reference_appendices/faq.html#how-do-i-see-all-the-inventory-variables-defined-for-my-host) |

### 문제

문서가 경고하거나 권하는 것은 여섯이다.

| 경고 | 원문 | 출처 |
|---|---|---|
| group마다 값이 다르면 Ansible이 안쪽 규칙으로 고른다 | "If you assign different values to the same variable in different groups, Ansible chooses which value to use based on internal rules for merging." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#assigning-a-variable-to-many-machines-group-variables) |
| 변수는 한곳에 정의한다 | "You should define each variable in one place." | [variables](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable) |
| 우선순위 규칙을 모르면 되레 해가 된다 | "This flexibility is convenient, but it can backfire if you do not understand the precedence rules." | [general precedence](https://docs.ansible.com/projects/ansible/latest/reference_appendices/general_precedence.html) |
| dictionary를 덮어쓰지 않고 합치게 하는 설정은 바꾸지 않는다 | "WARNING, changing this setting is not recommended as this is fragile and makes your content (plays, roles, collections) nonportable, leading to continual confusion and misuse." | [config](https://docs.ansible.com/projects/ansible/latest/reference_appendices/config.html#default-hash-behaviour) |
| 복잡하게 느껴지면 더 단순한 길을 찾는다 | "If something feels complicated, it probably is." | [tips](https://docs.ansible.com/projects/ansible/latest/tips_tricks/ansible_tips_tricks.html#keep-it-simple) |
| 환경 여럿을 한 파일에 두지 않는다 | "Keeping all your environments in one file can lead to surprises!" | [tips](https://docs.ansible.com/projects/ansible/latest/tips_tricks/ansible_tips_tricks.html#separate-production-and-staging-inventory) |

쓰는 사람이 겪은 문제는 ansible/ansible 저장소의 issue 넷에서 옮긴다.

| 겪은 문제 | 보고한 사람의 말 | maintainer의 답 | 출처 |
|---|---|---|---|
| host 하나가 group 둘에 들면, 한 group만 골라 실행해도 다른 group의 변수가 덮는다 | "group_vars should not be overwritten by another group when sharing the same host" | "closing as this is not a bug but by design, group vars get flattened per host and do not vary because of how you select the host" | [ansible #9065](https://github.com/ansible/ansible/issues/9065) (2014) |
| 위와 같다 | "group_vars and host_vars are override by last one in the inventory doc when a host belong to more than one group." | "This is not a bug, this is by design and clearly documented" | [ansible #49602](https://github.com/ansible/ansible/issues/49602) (2018) |
| `ansible_group_priority`를 `group_vars` 폴더에 두어서 듣지 않았다 | "it took me a lot of hair pulling to figure that out" | 답은 없다. 문서를 고치는 [PR #44865](https://github.com/ansible/ansible/pull/44865)가 merge된 때에 닫혔다 | [ansible #41512](https://github.com/ansible/ansible/issues/41512) (2018) |
| 부모 group에 준 `ansible_group_priority`가 자식 group에 내려가지 않는다 | "it is not passed down from group to child group" | "group priority is NOT meant to be inherited, its specific to the group it is defined in." | [ansible #34949](https://github.com/ansible/ansible/issues/34949) (2018) |

#9065를 보고한 사람은 같은 기계에 group마다 다른 이름을 붙여 host를 둘로 만드는 길로 돌아갔고, 그 길을 "highly error prone and is not ideal"이라고 적었다([ansible #9065](https://github.com/ansible/ansible/issues/9065)).

## issue #20의 주장과 견줌

issue #20이 확인하지 않은 주장으로 적은 셋을 문장 아홉으로 나누어 견준다.

| 주장 | 판정 | 근거 | 출처 |
|---|---|---|---|
| 계층형 DB는 다대다 관계를 복사 없이 담지 못했다 | 일부만 맞다 | tree만으로는 복제가 필요하다. IMS는 logical relationship으로 복제 없이 담는다 | [DSC 부록 E](https://www.db-book.com/db6/appendices-dir/e.pdf), [IMS logical relationship](https://www.ibm.com/docs/en/ims/15.6.0?topic=functions-creating-logical-relationships) |
| 그것이 관계형 model이 나온 까닭에 든다 | 문서에 없다 | Codd의 논문이 든 까닭은 data independence와 inconsistency다. tree의 복제는 적지 않는다 | [Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) |
| Active Directory는 GPO 하나를 OU 여럿에 link할 수 있다 | 맞다 | "A GPO can be linked to multiple Active Directory containers." | [GPMC](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-management-console#link-a-gpo) |
| 적용된 정책을 뽑아 보는 `gpresult`가 있다 | 맞다 | "Displays the Resultant Set of Policy (RSoP) information for a remote user and computer." | [gpresult](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/gpresult) |
| block inheritance와 enforced가 결과를 맞히기 어렵게 한다 | 맞다 | 문서의 말은 troubleshooting이 어려워진다는 것이다. #Group Policy의 경고 표 앞 세 행 | [New-GPLink](https://learn.microsoft.com/en-us/powershell/module/grouppolicy/new-gplink#-enforced), [Set-GPInheritance](https://learn.microsoft.com/en-us/powershell/module/grouppolicy/set-gpinheritance#notes) |
| Ansible은 group마다 `group_vars/<group>/` 폴더를 둔다 | 일부만 맞다 | 폴더는 세 방식 가운데 하나다. 파일 하나로도, inventory source 안에도 둔다 | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#organizing-host-and-group-variables) |
| host가 어느 group에 드는지는 inventory 파일에 적는다 | 맞다 | group 이름 아래에 host를 적는다. inventory는 파일 말고 plugin이 만들 수도 있다 | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#inventory-basics-formats-hosts-and-groups) |
| `group_vars/all`은 모든 host에 걸린다 | 맞다 | "The all group contains every host." | [inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html#default-groups) |
| 변수 우선순위의 단계가 많아서 결과를 맞히기 어렵다 | 단계가 많다는 것은 맞다. 맞히기 어렵다는 말은 문서에 없다 | 단계는 22개다. 문서의 말은 규칙을 모르면 "it can backfire"다. 옮긴 사용자 보고 넷은 22단계가 아니라 group끼리 합치는 순서에서 나왔다 | [variables](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence), [general precedence](https://docs.ansible.com/projects/ansible/latest/reference_appendices/general_precedence.html) |

Codd가 논문 첫머리에 적은 문제는 둘이다. 하나는 "the problems treated here are those of data independence"이고, 다른 하나는 "certain kinds of data inconsistency which are expected to become troublesome even in nondeductive systems"다([Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 1.1절).

Codd는 없애야 할 의존을 셋으로 든다. 원문은 "Three of the principal kinds of data dependencies which still need to be removed are: ordering dependence, indexing dependence, and access path dependence."다([Codd 1970](https://www.seas.upenn.edu/~zives/03f/cis550/codd.pdf) 1.2절).

문서는 inventory를 plugin으로 만드는 방식을 "You can generate an inventory dynamically."라고 적는다([inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html)).

## 확인하지 못한 것

| 모르는 것 | 문서가 적은 데까지 | 알아볼 방법 |
|---|---|---|
| Codd가 논문을 쓴 때의 IMS/360이 다대다 관계를 복제 없이 담았는지 | Codd는 그때의 IMS/360이 같은 domain이 둘인 relation을 담지 못한다고만 적는다. logical relationship을 적은 IBM 문서는 IMS 15.6의 것이다 | Codd의 참고문헌 5번인 IMS/360 Application Description Manual을 본다 |
| tree의 복제가 관계형 model이 나온 까닭에 드는지 | 1970년 논문에는 없다. Codd의 다른 글은 읽지 않았다 | Codd가 쓴 다른 글을 본다 |
| `gPLink` 값 안의 차례가 link order와 어느 방향으로 맞는지 | 두 문서가 어긋난다. GP scope는 새 link가 값의 맨 앞에 들고 "the latest policies linked are the most dominant"라고 적는다. New-GPLink는 새 link가 "the lowest precedence"로 든다고 적는다 | 시험용 domain에서 link 둘을 걸고 `gPLink` 값과 GPMC의 link order를 견준다 |
| GPO 하나를 OU 여럿에 link한 것 때문에 생긴 문제의 사용자 보고 | 옮긴 보고는 block inheritance와 security filtering 쪽이다. 여러 곳에 link한 것을 원인으로 적은 보고는 찾지 못했다 | Microsoft Q&A와 지원 글을 더 찾는다 |
| junction table을 쓰는 사람이 낸 문제 보고 | Codd가 적은 connection trap과 PostgreSQL 문서의 주의까지 옮겼다. 사용자 보고는 찾지 않았다 | PostgreSQL mailing list의 보고를 찾는다 |
| Ansible issue의 동작이 지금 version에서도 같은지 | 보고는 2014~2018년의 것이다. version 14 문서도 변수를 host 단위로 편다고 적는다 | #9065의 inventory로 `ansible-inventory --host`를 돌려 본다 |
| 보관된 Microsoft 문서의 문장이 지금 Windows에서도 맞는지 | 충돌을 설정마다 푼다는 문장과 security group이 link한 container 안에서만 좁힌다는 문장은 보관된 문서에만 있다 | 시험용 domain에서 `gpresult`로 본다 |

## 새 질문 후보

- 세 시스템의 순서 규칙은 같은 이름의 설정이나 변수가 겹칠 때 이기는 쪽을 정한다. markdown 기억에는 겹칠 이름이 없는데, 걸치는 기억을 load할 때 정해야 하는 순서가 있는가. 걸치는 기억을 둘 자리를 정할 때 순서 규칙까지 들여올지에 쓰인다.
- 파일 시스템의 hard link와 symbolic link는 tree에 걸치는 파일의 소속을 어디에 적고, 쓰는 사람은 어떤 문제를 겪었는가. `~/.mem`이 폴더 tree여서 넷째 사례가 된다.
- Ansible은 group의 변수를 host에 펴서, 고르지 않은 group의 변수도 그 host에 걸린다. 걸치는 기억의 소속을 작업 위치에 붙이면 같은 모양의 문제가 생기는가.
