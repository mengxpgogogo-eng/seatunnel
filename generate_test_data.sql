-- ============================================
-- 生成 api_call_log 表 300万测试数据脚本
-- ============================================
-- 使用方法：
-- 1. 连接到 MySQL: mysql -u用户名 -p数据库名 < generate_test_data.sql
-- 2. 或者直接在 MySQL 客户端中执行此脚本
-- ============================================

USE test_medical_data_management;

-- 设置会话变量
SET SESSION sql_log_bin = 0;  -- 如果有 binlog，可以关闭以提高速度
SET SESSION autocommit = 0;   -- 关闭自动提交，批量提交提高性能

-- 清理存储过程（如果存在）
DROP PROCEDURE IF EXISTS generate_api_call_log_data;

DELIMITER $$

CREATE PROCEDURE generate_api_call_log_data(
    IN total_records INT
)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE batch_size INT DEFAULT 10000;  -- 每批插入1万条
    DECLARE batch_count INT;
    DECLARE start_time DATETIME DEFAULT NOW();
    
    SET batch_count = CEIL(total_records / batch_size);
    
    -- 预定义一些测试数据
    DECLARE done INT DEFAULT 0;
    
    WHILE i < total_records DO
        -- 批量插入
        INSERT INTO api_call_log (
            api_config_id,
            api_path,
            token,
            user_id,
            request_params,
            execute_sql,
            response_status,
            response_result,
            error_msg,
            execution_time,
            call_time
        )
        SELECT
            -- api_config_id: 1-100 之间随机
            FLOOR(1 + RAND() * 100) AS api_config_id,
            
            -- api_path: 随机路径
            CONCAT(
                '/api/v', FLOOR(1 + RAND() * 3),
                '/', CASE FLOOR(RAND() * 5)
                    WHEN 0 THEN 'user'
                    WHEN 1 THEN 'order'
                    WHEN 2 THEN 'product'
                    WHEN 3 THEN 'payment'
                    ELSE 'medical'
                END,
                '/', CASE FLOOR(RAND() * 3)
                    WHEN 0 THEN 'query'
                    WHEN 1 THEN 'create'
                    ELSE 'update'
                END
            ) AS api_path,
            
            -- token: 随机32位字符串
            CONCAT(
                SUBSTRING(MD5(RAND()), 1, 8), '-',
                SUBSTRING(MD5(RAND()), 1, 4), '-',
                SUBSTRING(MD5(RAND()), 1, 4), '-',
                SUBSTRING(MD5(RAND()), 1, 4), '-',
                SUBSTRING(MD5(RAND()), 1, 12)
            ) AS token,
            
            -- user_id: 1-10000 之间的用户ID
            CAST(FLOOR(1 + RAND() * 10000) AS CHAR) AS user_id,
            
            -- request_params: 随机JSON参数
            CONCAT(
                '{"patient_id":', FLOOR(1000 + RAND() * 9000),
                ',"doctor_id":', FLOOR(100 + RAND() * 900),
                ',"department":"', CASE FLOOR(RAND() * 5)
                    WHEN 0 THEN '内科'
                    WHEN 1 THEN '外科'
                    WHEN 2 THEN '儿科'
                    WHEN 3 THEN '妇科'
                    ELSE '骨科'
                END, '"}'
            ) AS request_params,
            
            -- execute_sql: 随机SQL语句
            CONCAT(
                'SELECT * FROM medical_records WHERE patient_id = ',
                FLOOR(1000 + RAND() * 9000),
                ' AND status = ',
                FLOOR(RAND() * 3),
                ' LIMIT 100'
            ) AS execute_sql,
            
            -- response_status: 80% 成功，20% 失败
            IF(RAND() < 0.8, 1, 0) AS response_status,
            
            -- response_result: 成功时有结果，失败时为null
            IF(RAND() < 0.8, 
                CONCAT('{"code":200,"data":{"count":', FLOOR(1 + RAND() * 100), '},"message":"success"}'),
                NULL
            ) AS response_result,
            
            -- error_msg: 失败时有错误信息
            IF(RAND() >= 0.8,
                CASE FLOOR(RAND() * 4)
                    WHEN 0 THEN '数据库连接超时'
                    WHEN 1 THEN '参数验证失败'
                    WHEN 2 THEN '业务逻辑错误'
                    ELSE '系统内部错误'
                END,
                NULL
            ) AS error_msg,
            
            -- execution_time: 50-5000 毫秒之间
            FLOOR(50 + RAND() * 4950) AS execution_time,
            
            -- call_time: 最近30天内的随机时间
            DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 30) DAY) + 
            INTERVAL FLOOR(RAND() * 24) HOUR +
            INTERVAL FLOOR(RAND() * 60) MINUTE +
            INTERVAL FLOOR(RAND() * 60) SECOND AS call_time
            
        FROM (
            SELECT a.N + b.N * 10 + c.N * 100 + d.N * 1000 AS num
            FROM 
                (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
                (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
                (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c,
                (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) d
        ) numbers
        WHERE numbers.num < LEAST(batch_size, total_records - i)
        LIMIT LEAST(batch_size, total_records - i);
        
        SET i = i + batch_size;
        
        -- 每10万条提交一次
        IF i % 100000 = 0 THEN
            COMMIT;
            SELECT CONCAT('已生成 ', i, ' 条记录，进度: ', ROUND(i / total_records * 100, 2), '%') AS progress;
        END IF;
        
    END WHILE;
    
    COMMIT;
    
    SELECT CONCAT(
        '数据生成完成！总记录数: ', total_records, 
        ', 耗时: ', TIMESTAMPDIFF(SECOND, start_time, NOW()), ' 秒'
    ) AS result;
    
END$$

DELIMITER ;

-- 执行生成 300万条数据
-- 注意：这可能需要较长时间（预计5-15分钟，取决于服务器性能）

SELECT '开始生成 300万条测试数据，请耐心等待...' AS info;
SELECT NOW() AS start_time;

-- 调用存储过程生成数据
CALL generate_api_call_log_data(3000000);

SELECT NOW() AS end_time;

-- 验证数据
SELECT 
    COUNT(*) AS total_records,
    MIN(call_time) AS earliest_time,
    MAX(call_time) AS latest_time,
    COUNT(DISTINCT user_id) AS distinct_users,
    COUNT(DISTINCT api_config_id) AS distinct_api_configs,
    SUM(CASE WHEN response_status = 1 THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN response_status = 0 THEN 1 ELSE 0 END) AS failure_count
FROM api_call_log;

-- 清理存储过程
DROP PROCEDURE IF EXISTS generate_api_call_log_data;

-- 恢复设置
SET SESSION autocommit = 1;
SET SESSION sql_log_bin = 1;

SELECT '脚本执行完成！' AS info;


