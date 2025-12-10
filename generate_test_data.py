#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 api_call_log 表 300万测试数据脚本 (Python版本)
性能更优，可以控制批次大小和进度显示

使用方法:
    python3 generate_test_data.py

依赖:
    pip install pymysql

或者修改为使用 mysql-connector-python:
    pip install mysql-connector-python
"""

import random
import string
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional

# 数据库配置
DB_CONFIG = {
    'host': '192.168.16.122',
    'port': 3308,
    'user': 'test_medical_data_management',
    'password': 'K1sj3831fN',
    'database': 'test_medical_data_management',
    'charset': 'utf8mb4'
}

# 生成参数
TOTAL_RECORDS = 3000000  # 总记录数
BATCH_SIZE = 10000       # 每批插入的记录数（可根据内存调整：5000-20000）

# 尝试导入 pymysql，如果没有则使用 mysql-connector
try:
    import pymysql
    USE_PYMYSQL = True
except ImportError:
    try:
        import mysql.connector
        USE_PYMYSQL = False
    except ImportError:
        print("错误: 请安装数据库驱动!")
        print("pip install pymysql")
        print("或者: pip install mysql-connector-python")
        exit(1)


def generate_random_string(length: int) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_token() -> str:
    """生成类似UUID格式的token"""
    parts = [
        generate_random_string(8),
        generate_random_string(4),
        generate_random_string(4),
        generate_random_string(4),
        generate_random_string(12)
    ]
    return '-'.join(parts)


def generate_api_path() -> str:
    """生成随机的API路径"""
    versions = ['v1', 'v2', 'v3']
    modules = ['user', 'order', 'product', 'payment', 'medical']
    actions = ['query', 'create', 'update', 'delete', 'list']
    
    version = random.choice(versions)
    module = random.choice(modules)
    action = random.choice(actions)
    
    return f'/api/{version}/{module}/{action}'


def generate_request_params() -> str:
    """生成随机请求参数JSON"""
    departments = ['内科', '外科', '儿科', '妇科', '骨科', '眼科', '耳鼻喉科']
    patient_id = random.randint(1000, 9999)
    doctor_id = random.randint(100, 999)
    department = random.choice(departments)
    
    return f'{{"patient_id":{patient_id},"doctor_id":{doctor_id},"department":"{department}"}}'


def generate_execute_sql() -> str:
    """生成随机SQL语句"""
    patient_id = random.randint(1000, 9999)
    status = random.randint(0, 2)
    limit = random.randint(10, 200)
    
    return f'SELECT * FROM medical_records WHERE patient_id = {patient_id} AND status = {status} LIMIT {limit}'


def generate_response_result() -> Optional[str]:
    """生成响应结果"""
    count = random.randint(1, 100)
    return f'{{"code":200,"data":{{"count":{count}}},"message":"success"}}'


def generate_error_msg() -> Optional[str]:
    """生成错误信息"""
    errors = [
        '数据库连接超时',
        '参数验证失败: 缺少必填字段',
        '业务逻辑错误: 数据不存在',
        '系统内部错误: 服务暂时不可用',
        '权限验证失败: 无访问权限'
    ]
    return random.choice(errors)


def generate_call_time() -> datetime:
    """生成最近30天内的随机时间"""
    days_ago = random.randint(0, 30)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    seconds_ago = random.randint(0, 59)
    
    return datetime.now() - timedelta(
        days=days_ago,
        hours=hours_ago,
        minutes=minutes_ago,
        seconds=seconds_ago
    )


def generate_batch_data(batch_size: int) -> list:
    """生成一批测试数据"""
    batch = []
    
    for _ in range(batch_size):
        is_success = random.random() < 0.8  # 80% 成功率
        
        record = (
            random.randint(1, 100),           # api_config_id
            generate_api_path(),               # api_path
            generate_token(),                  # token
            str(random.randint(1, 10000)),     # user_id
            generate_request_params(),         # request_params
            generate_execute_sql(),            # execute_sql
            1 if is_success else 0,           # response_status
            generate_response_result() if is_success else None,  # response_result
            generate_error_msg() if not is_success else None,    # error_msg
            random.randint(50, 5000),         # execution_time (毫秒)
            generate_call_time()               # call_time
        )
        batch.append(record)
    
    return batch


def insert_batch(cursor, batch: list) -> None:
    """批量插入数据"""
    sql = """
    INSERT INTO api_call_log (
        api_config_id, api_path, token, user_id, request_params,
        execute_sql, response_status, response_result, error_msg,
        execution_time, call_time
    ) VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s
    )
    """
    cursor.executemany(sql, batch)


def main():
    """主函数"""
    print("=" * 60)
    print("开始生成 api_call_log 表测试数据")
    print("=" * 60)
    print(f"总记录数: {TOTAL_RECORDS:,}")
    print(f"批次大小: {BATCH_SIZE:,}")
    print(f"预计批次数: {TOTAL_RECORDS // BATCH_SIZE}")
    print("=" * 60)
    
    # 连接数据库
    try:
        if USE_PYMYSQL:
            conn = pymysql.connect(**DB_CONFIG)
        else:
            conn = mysql.connector.connect(**DB_CONFIG)
        
        cursor = conn.cursor()
        print(f"✓ 数据库连接成功: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return
    
    start_time = time.time()
    total_inserted = 0
    
    try:
        # 关闭自动提交，提高性能
        conn.autocommit = False
        
        # 生成并插入数据
        batch_count = 0
        while total_inserted < TOTAL_RECORDS:
            current_batch_size = min(BATCH_SIZE, TOTAL_RECORDS - total_inserted)
            
            # 生成一批数据
            batch = generate_batch_data(current_batch_size)
            
            # 插入数据
            insert_batch(cursor, batch)
            
            # 每10批提交一次（或者每10万条）
            batch_count += 1
            total_inserted += len(batch)
            
            if batch_count % 10 == 0 or total_inserted >= TOTAL_RECORDS:
                conn.commit()
                elapsed = time.time() - start_time
                progress = (total_inserted / TOTAL_RECORDS) * 100
                speed = total_inserted / elapsed if elapsed > 0 else 0
                eta = (TOTAL_RECORDS - total_inserted) / speed if speed > 0 else 0
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"已插入: {total_inserted:>10,} / {TOTAL_RECORDS:,} "
                      f"({progress:>5.2f}%) | "
                      f"速度: {speed:>8,.0f} 条/秒 | "
                      f"预计剩余: {int(eta)} 秒")
        
        # 最终提交
        conn.commit()
        
        # 统计信息
        elapsed_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("数据生成完成！")
        print("=" * 60)
        print(f"总记录数: {total_inserted:,}")
        print(f"总耗时: {elapsed_time:.2f} 秒 ({elapsed_time/60:.2f} 分钟)")
        print(f"平均速度: {total_inserted/elapsed_time:,.0f} 条/秒")
        
        # 验证数据
        print("\n正在验证数据...")
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_records,
                MIN(call_time) AS earliest_time,
                MAX(call_time) AS latest_time,
                COUNT(DISTINCT user_id) AS distinct_users,
                COUNT(DISTINCT api_config_id) AS distinct_api_configs,
                SUM(CASE WHEN response_status = 1 THEN 1 ELSE 0 END) AS success_count,
                SUM(CASE WHEN response_status = 0 THEN 1 ELSE 0 END) AS failure_count
            FROM api_call_log
        """)
        
        result = cursor.fetchone()
        print("\n数据统计:")
        print(f"  总记录数: {result[0]:,}")
        print(f"  最早时间: {result[1]}")
        print(f"  最晚时间: {result[2]}")
        print(f"  不同用户数: {result[3]:,}")
        print(f"  不同API配置数: {result[4]:,}")
        print(f"  成功记录: {result[5]:,} ({result[5]/result[0]*100:.2f}%)")
        print(f"  失败记录: {result[6]:,} ({result[6]/result[0]*100:.2f}%)")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cursor.close()
        conn.close()
        print("\n数据库连接已关闭")


if __name__ == '__main__':
    main()
