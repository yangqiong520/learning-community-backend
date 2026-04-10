from flask import Blueprint, request, jsonify
from libs.db import db
from app.models.homework import HomeworkType, Homework, HomeworkVersion, ExcellentHomework, ProblemHomework
from app.models.user import User
from app.models.homework_like import HomeworkLike
from app.models.course import Course
from libs.jwt_auth import token_required
from libs.response import success_response, error_response, not_found_response

homework_bp = Blueprint('homeworks', __name__)

@homework_bp.route('/types', methods=['GET'])
@token_required
def get_homework_types():
    try:
        user = User.query.get(request.current_user_id)
        course_id = request.args.get('course_id', type=int)
        
        # 打印调试信息
        print(f"[DEBUG] 获取作业类型 - 用户ID: {request.current_user_id}, 用户角色: {user.role}, 请求的course_id: {course_id}")
        
        query = HomeworkType.query.filter_by(is_active=True)
        
        if course_id:
            query = query.filter_by(course_id=course_id)
            print(f"[DEBUG] 按课程ID {course_id} 筛选")
        else:
            # 如果没有指定课程ID，学生应该看到所有课程的作业类型
            print(f"[DEBUG] 未指定课程ID，返回所有激活的作业类型")
        
        types = query.order_by(HomeworkType.created_at.desc()).all()
        
        print(f"[DEBUG] 找到 {len(types)} 个作业类型")
        for t in types:
            print(f"[DEBUG] 作业类型: ID={t.id}, 课程ID={t.course_id}, 名称={t.name}, 教师ID={t.teacher_id}")
        
        result = [type.to_dict() for type in types]
        return success_response('获取作业类型成功', result)
    except Exception as e:
        print(f"[ERROR] 获取作业类型失败: {str(e)}")
        return error_response(f'获取作业类型失败: {str(e)}')

@homework_bp.route('/types', methods=['POST'])
@token_required
def create_homework_type():
    try:
        print(f"\n{'='*60}")
        print(f"[DEBUG] 收到 POST /types 请求")
        print(f"[DEBUG] 请求方法: {request.method}")
        print(f"[DEBUG] 请求路径: {request.path}")
        print(f"[DEBUG] 请求头: {dict(request.headers)}")
        print(f"[DEBUG] 请求体原始数据: {request.get_data(as_text=True)}")

        data = request.get_json()
        print(f"[DEBUG] 解析后的JSON数据: {data}")

        if not data:
            print(f"[ERROR] 请求数据为空！")
            return error_response('请求数据不能为空')

        course_id = data.get('course_id')
        course_name = data.get('course_name')
        name = data.get('name')
        content = data.get('content')

        print(f"[DEBUG] course_id: {course_id}, course_name: {course_name}, name: {name}, content: {content}")

        # 检查名称和内容不能为空
        if not name or not content:
            print(f"[ERROR] 作业类型名称和内容不能为空！")
            return error_response('作业类型名称和内容不能为空')
        
        # 处理课程ID或课程名称
        final_course_id = None
        
        # 优先使用 course_id（保持向后兼容）
        if course_id:
            try:
                final_course_id = int(course_id)
                # 验证课程是否存在
                course = Course.query.get(final_course_id)
                if not course:
                    return error_response('指定的课程不存在')
                # 验证权限：只能使用自己创建的课程
                if course.teacher_id != request.current_user_id:
                    return error_response('无权限使用此课程', 403)
                print(f"[DEBUG] 使用指定课程ID: {final_course_id}")
            except (ValueError, TypeError):
                return error_response('课程ID必须是整数')
        elif course_name:
            # 通过课程名称查找或创建课程
            course = Course.query.filter_by(
                teacher_id=request.current_user_id,
                name=course_name,
                is_active=True
            ).first()
            
            if course:
                # 找到同名课程，直接使用
                final_course_id = course.id
                print(f"[DEBUG] 找到同名课程，使用课程ID: {final_course_id}")
            else:
                # 未找到，自动创建新课程
                course = Course(
                    name=course_name,
                    teacher_id=request.current_user_id
                )
                db.session.add(course)
                db.session.flush()  # 获取ID但不提交
                final_course_id = course.id
                print(f"[DEBUG] 创建新课程，课程ID: {final_course_id}")
        else:
            # 两者都没提供
            return error_response('必须指定课程ID或课程名称')

        # 检查同一课程下是否已存在同名作业类型
        existing_type = HomeworkType.query.filter_by(
            course_id=final_course_id,
            name=name,
            is_active=True
        ).first()

        if existing_type:
            course_info = Course.query.get(final_course_id)
            course_name_str = course_info.name if course_info else '该课程'
            print(f"[ERROR] 同一课程下已存在同名作业类型: 课程={course_name_str}, 作业类型={name}")
            return error_response(
                f'课程"{course_name_str}"下已存在作业类型"{name}"，请使用不同的名称或更新现有作业类型',
                409
            )

        # 创建作业类型
        homework_type = HomeworkType(
            course_id=final_course_id,
            name=name,
            content=content,
            teacher_id=request.current_user_id
        )

        db.session.add(homework_type)
        db.session.commit()

        print(f"[OK] 作业类型创建成功: ID={homework_type.id}, 课程ID={final_course_id}, 名称={name}")
        return success_response('创建作业类型成功', {
            'id': homework_type.id,
            'course_id': final_course_id,
            'course_name': course_name if course_name else Course.query.get(final_course_id).name
        })
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] 创建作业类型失败: {str(e)}")
        return error_response(f'创建作业类型失败: {str(e)}')

@homework_bp.route('/types/<int:type_id>', methods=['PUT'])
@token_required
def update_homework_type(type_id):
    try:
        homework_type = HomeworkType.query.get(type_id)
        if not homework_type:
            return not_found_response('作业类型不存在')
        
        if homework_type.teacher_id != request.current_user_id:
            return error_response('无权限修改此作业类型', 403)
        
        data = request.get_json()
        name = data.get('name')
        content = data.get('content')
        is_active = data.get('is_active')
        
        if name:
            homework_type.name = name
        if content:
            homework_type.content = content
        if is_active is not None:
            homework_type.is_active = is_active
        
        db.session.commit()
        
        return success_response('更新作业类型成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新作业类型失败: {str(e)}')

@homework_bp.route('/types/<int:type_id>', methods=['DELETE'])
@token_required
def delete_homework_type(type_id):
    try:
        homework_type = HomeworkType.query.get(type_id)
        if not homework_type:
            return not_found_response('作业类型不存在')
        
        if homework_type.teacher_id != request.current_user_id:
            return error_response('无权限删除此作业类型', 403)
        
        homework_type.is_active = False
        db.session.commit()
        
        return success_response('删除作业类型成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除作业类型失败: {str(e)}')

@homework_bp.route('/student', methods=['GET'])
@token_required
def get_student_homeworks():
    try:
        user = User.query.get(request.current_user_id)
        if user.role != User.ROLE_STUDENT:
            return error_response('仅学生可查看作业列表', 403)
        
        course_id = request.args.get('course_id', type=int)
        status = request.args.get('status')
        
        query = Homework.query.filter_by(
            student_id=request.current_user_id,
            is_active=True
        )
        
        if course_id:
            query = query.filter_by(course_id=course_id)
        if status:
            query = query.filter_by(status=status)
        
        homeworks = query.order_by(Homework.created_at.desc()).all()
        
        result = [homework.to_dict() for homework in homeworks]
        return success_response('获取学生作业列表成功', result)
    except Exception as e:
        return error_response(f'获取学生作业列表失败: {str(e)}')

@homework_bp.route('/<int:homework_id>/versions', methods=['GET'])
@token_required
def get_homework_versions(homework_id):
    """
    获取作业的所有版本历史
    """
    try:
        user = User.query.get(request.current_user_id)
        
        homework = Homework.query.get(homework_id)
        if not homework:
            return not_found_response('作业不存在')
        
        # 检查权限：学生只能看自己的作业，教师可以看所有作业
        if user.role == User.ROLE_STUDENT and homework.student_id != request.current_user_id:
            return error_response('无权限查看此作业的版本', 403)
        
        # 获取所有版本，按版本号倒序排列
        versions = HomeworkVersion.query.filter_by(
            homework_id=homework_id
        ).order_by(HomeworkVersion.version_number.desc()).all()
        
        result = [version.to_dict() for version in versions]
        return success_response('获取作业版本历史成功', result)
    except Exception as e:
        return error_response(f'获取作业版本历史失败: {str(e)}')

@homework_bp.route('', methods=['POST'])
@token_required
def create_homework():
    try:
        user = User.query.get(request.current_user_id)
        if user.role != User.ROLE_STUDENT:
            return error_response('仅学生可提交作业', 403)
        
        data = request.get_json()
        course_id = data.get('course_id')
        homework_type_id = data.get('homework_type_id')
        file_id = data.get('file_id')
        
        if not course_id or not homework_type_id or not file_id:
            return error_response('课程ID、作业类型ID和文件ID不能为空')
        
        homework = Homework(
            student_id=request.current_user_id,
            course_id=course_id,
            homework_type_id=homework_type_id,
            status=Homework.STATUS_DRAFT
        )
        
        db.session.add(homework)
        db.session.flush()
        
        version = HomeworkVersion(
            homework_id=homework.id,
            version_number=1,
            file_file_id=file_id
        )
        
        db.session.add(version)
        db.session.flush()
        
        homework.current_version_id = version.id
        db.session.commit()
        
        return success_response('创建作业成功', {'id': homework.id})
    except Exception as e:
        db.session.rollback()
        return error_response(f'创建作业失败: {str(e)}')

@homework_bp.route('/<int:homework_id>', methods=['PUT'])
@token_required
def update_homework(homework_id):
    try:
        homework = Homework.query.get(homework_id)
        if not homework:
            return not_found_response('作业不存在')
        
        if homework.student_id != request.current_user_id:
            return error_response('无权限修改此作业', 403)
        
        data = request.get_json()
        file_id = data.get('file_id')
        status = data.get('status')
        
        if status:
            homework.status = status
        
        if file_id:
            current_version = HomeworkVersion.query.get(homework.current_version_id)
            if current_version:
                new_version_number = current_version.version_number + 1
            else:
                new_version_number = 1
            
            version = HomeworkVersion(
                homework_id=homework.id,
                version_number=new_version_number,
                file_file_id=file_id
            )
            
            db.session.add(version)
            db.session.flush()
            
            homework.current_version_id = version.id
        
        db.session.commit()
        
        return success_response('更新作业成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新作业失败: {str(e)}')

@homework_bp.route('/<int:homework_id>/submit', methods=['POST'])
@token_required
def submit_homework(homework_id):
    try:
        homework = Homework.query.get(homework_id)
        if not homework:
            return not_found_response('作业不存在')
        
        if homework.student_id != request.current_user_id:
            return error_response('无权限提交此作业', 403)
        
        homework.status = Homework.STATUS_SUBMITTED
        db.session.commit()
        
        return success_response('提交作业成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'提交作业失败: {str(e)}')

@homework_bp.route('/<int:homework_id>/evaluate', methods=['POST'])
@token_required
def evaluate_homework(homework_id):
    try:
        user = User.query.get(request.current_user_id)
        if user.role != User.ROLE_TEACHER:
            return error_response('仅教师可批改作业', 403)
        
        homework = Homework.query.get(homework_id)
        if not homework:
            return not_found_response('作业不存在')
        
        data = request.get_json()
        evaluation = data.get('evaluation')
        score = data.get('score')
        is_excellent = data.get('is_excellent', False)
        is_problem = data.get('is_problem', False)
        is_redo = data.get('is_redo', False)
        
        if not evaluation and not score:
            return error_response('评价或分数至少需要一个')
        
        version = HomeworkVersion.query.get(homework.current_version_id)
        if not version:
            return error_response('作业版本不存在')
        
        if evaluation:
            version.evaluation = evaluation
        if score:
            version.score = score
        version.is_redo = is_redo
        
        if is_excellent:
            homework.status = Homework.STATUS_EXCELLENT
        elif is_problem:
            homework.status = Homework.STATUS_PROBLEM
        else:
            homework.status = Homework.STATUS_RETURNED
        
        db.session.commit()
        
        return success_response('批改作业成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'批改作业失败: {str(e)}')

@homework_bp.route('/excellent', methods=['GET'])
@token_required
def get_excellent_homeworks():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        query = ExcellentHomework.query
        
        excellent_homeworks = query.order_by(ExcellentHomework.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = [homework.to_dict(user_id=request.current_user_id) for homework in excellent_homeworks.items]
        
        return success_response('获取优秀作业列表成功', {
            'data': result,
            'total': excellent_homeworks.total,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        return error_response(f'获取优秀作业列表失败: {str(e)}')

@homework_bp.route('/excellent/<int:excellent_id>/like', methods=['POST'])
@token_required
def like_excellent_homework(excellent_id):
    try:
        excellent_homework = ExcellentHomework.query.get(excellent_id)
        if not excellent_homework:
            return not_found_response('优秀作业不存在')
        
        like = HomeworkLike.query.filter_by(
            user_id=request.current_user_id,
            excellent_homework_id=excellent_id
        ).first()
        
        if like:
            like.is_liked = not like.is_liked
        else:
            like = HomeworkLike(
                user_id=request.current_user_id,
                excellent_homework_id=excellent_id,
                is_liked=True
            )
            db.session.add(like)
        
        if like.is_liked:
            excellent_homework.likes_count += 1
        else:
            excellent_homework.likes_count -= 1
        
        db.session.commit()
        
        return success_response('操作成功', {'is_liked': like.is_liked})
    except Exception as e:
        db.session.rollback()
        return error_response(f'操作失败: {str(e)}')

@homework_bp.route('/favorites', methods=['GET'])
@token_required
def get_favorites():
    """获取当前用户收藏的优秀作业列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        # 查询用户收藏的优秀作业，按收藏时间倒序，支持分页
        likes = HomeworkLike.query.filter_by(
            user_id=request.current_user_id,
            is_liked=True
        ).order_by(HomeworkLike.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 构建结果列表
        result = []
        for like in likes.items:
            if like.excellent_homework_id:
                excellent_homework = ExcellentHomework.query.get(like.excellent_homework_id)
                if excellent_homework:
                    item = excellent_homework.to_dict(user_id=request.current_user_id)
                    # 添加收藏时间
                    if like.created_at:
                        item['favorite_time'] = f"{like.created_at.year}.{like.created_at.month}.{like.created_at.day}"
                    else:
                        item['favorite_time'] = None
                    result.append(item)
        
        return success_response('获取收藏列表成功', {
            'excellent_homeworks': result,
            'total': likes.total,
            'page': page,
            'per_page': per_page,
            'pages': likes.pages
        })
    except Exception as e:
        return error_response(f'获取收藏列表失败: {str(e)}')
