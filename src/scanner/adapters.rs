/// Tree-Sitter Language Adapters
/// Generates language-specific S-expression queries for Tree-Sitter AST inspection.

pub trait LanguageAdapter {
    fn language_id(&self) -> &'static str;
    fn extensions(&self) -> &'static [&'static str];
    fn dangerous_call_query(&self) -> &'static str;
    fn logging_check_query(&self) -> &'static str;
}

pub struct PythonAdapter;
pub struct TypeScriptAdapter;

impl LanguageAdapter for PythonAdapter {
    fn language_id(&self) -> &'static str {
        "python"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &[".py", ".pyw"]
    }

    fn dangerous_call_query(&self) -> &'static str {
        r#"(call
            function: (identifier) @func_name
            (#match? @func_name "^(eval|exec|os\.system|subprocess\.run|call_tool|invoke_agent)$")
        ) @dangerous_call"#
    }

    fn logging_check_query(&self) -> &'static str {
        r#"(call
            function: (identifier) @func_name (#match? @func_name "^(execute_agent_action|dispatch_tool)$")
            arguments: (argument_list
                (keyword_argument
                    name: (identifier) @log_param (#eq? @log_param "enable_audit_log")
                    value: (false) @disabled_log
                )
            )
        ) @logging_disabled"#
    }
}

impl LanguageAdapter for TypeScriptAdapter {
    fn language_id(&self) -> &'static str {
        "typescript"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &[".ts", ".tsx", ".js", ".jsx", ".mjs"]
    }

    fn dangerous_call_query(&self) -> &'static str {
        r#"(call_expression
            function: (identifier) @func_name
            (#match? @func_name "^(eval|exec|child_process|invokeAgent|executeTool)$")
        ) @dangerous_call"#
    }

    fn logging_check_query(&self) -> &'static str {
        r#"(call_expression
            function: (identifier) @func_name (#match? @func_name "^(executeAgentAction|dispatchTool)$")
            arguments: (arguments
                (object
                    (pair
                        key: (property_identifier) @log_param (#eq? @log_param "enableAuditLog")
                        value: (false) @disabled_log
                    )
                )
            )
        ) @logging_disabled"#
    }
}
