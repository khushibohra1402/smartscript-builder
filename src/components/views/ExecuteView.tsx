import { useState } from 'react';
import { ConfigurationPanel } from '@/components/execute/ConfigurationPanel';
import { DescriptionInput } from '@/components/execute/DescriptionInput';
import { TestConfiguration, ExecutionResult } from '@/types/automation';
import { useToast } from '@/hooks/use-toast';
import { useGenerateScript, useValidateDevice, useExecuteTest, useSaveTestCase } from '@/hooks/useApi';

const initialConfig: TestConfiguration = {
  project: null,
  deviceType: 'web',
  platform: 'chrome',
  testType: 'functional',
  testCaseName: '',
  description: '',
};

interface ExecuteViewProps {
  onExecutionComplete: (result: ExecutionResult) => void;
}

export function ExecuteView({ onExecutionComplete }: ExecuteViewProps) {
  const [config, setConfig] = useState<TestConfiguration>(initialConfig);
  const [deviceValidated, setDeviceValidated] = useState(false);
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  const [savedTestCaseId, setSavedTestCaseId] = useState<string | null>(null);
  const { toast } = useToast();

  // API Hooks
  const validateDeviceMutation = useValidateDevice();
  const generateScriptMutation = useGenerateScript();
  const saveTestCaseMutation = useSaveTestCase();
  const executeTestMutation = useExecuteTest();

  const handleValidateDevice = async () => {
    try {
      const result = await validateDeviceMutation.mutateAsync({
        device_type: config.deviceType,
        platform: config.platform,
      });
      
      if (result.is_valid) {
        setDeviceValidated(true);
        toast({
          title: "Device Connected",
          description: result.message || `${config.platform} is ready for testing.`,
        });
      } else {
        toast({
          title: "Device Validation Failed",
          description: result.message || "Could not connect to device.",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Connection Error",
        description: error instanceof Error ? error.message : "Failed to validate device. Is the backend running?",
        variant: "destructive",
      });
    }
  };

  const handleGenerate = async () => {
    if (!config.project) {
      toast({
        title: "No Project Selected",
        description: "Please select a project first.",
        variant: "destructive",
      });
      return;
    }

    try {
      const result = await generateScriptMutation.mutateAsync({
        project_id: config.project.id,
        description: config.description,
        device_type: config.deviceType,
        platform: config.platform,
        test_type: config.testType,
      });

      setGeneratedCode(result.script_code);
      
      if (result.is_valid) {
        toast({
          title: "Script Generated",
          description: `Generated in ${result.generation_time_ms.toFixed(0)}ms. Review and execute.`,
        });
      } else {
        toast({
          title: "Script Generated with Warnings",
          description: result.validation_errors?.join(', ') || "Script has validation issues.",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Generation Failed",
        description: error instanceof Error ? error.message : "Failed to generate script. Is Ollama running?",
        variant: "destructive",
      });
    }
  };

  const handleExecute = async () => {
    if (!config.project || !generatedCode) {
      toast({
        title: "Cannot Execute",
        description: "Generate a script first.",
        variant: "destructive",
      });
      return;
    }

    try {
      // First, save the test case if not already saved
      let testCaseId = savedTestCaseId;
      
      if (!testCaseId) {
        const savedTestCase = await saveTestCaseMutation.mutateAsync({
          project_id: config.project.id,
          name: config.testCaseName || 'Untitled Test',
          description: config.description,
          device_type: config.deviceType,
          platform: config.platform,
          test_type: config.testType,
          script_code: generatedCode,
        });
        testCaseId = savedTestCase.id;
        setSavedTestCaseId(testCaseId);
      }

      toast({
        title: "Execution Started",
        description: "Your test is now running...",
      });

      // Execute the test
      const apiResult = await executeTestMutation.mutateAsync({
        test_case_id: testCaseId,
      });

      // Map API response to frontend ExecutionResult type
      const result: ExecutionResult = {
        execution_id: apiResult.execution_id,
        status: apiResult.status,
        testName: apiResult.test_name,
        projectName: apiResult.project_name,
        metrics: {
          total_duration: apiResult.metrics.total_duration,
          avg_response_time: apiResult.metrics.avg_response_time,
          step_success_rate: apiResult.metrics.step_success_rate,
        },
        steps: apiResult.steps.map((step, index) => ({
          id: `step-${index}`,
          action: step.action,
          result: step.result,
          latency: step.latency,
          error: step.error || null,
          timestamp: new Date().toISOString(),
        })),
        artifacts: {
          video_path: apiResult.artifacts.video_path,
          screenshot_failure: apiResult.artifacts.screenshot_failure || null,
        },
        ai_analysis: apiResult.ai_analysis,
        createdAt: apiResult.created_at,
      };

      onExecutionComplete(result);
    } catch (error) {
      toast({
        title: "Execution Failed",
        description: error instanceof Error ? error.message : "Test execution failed.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <ConfigurationPanel
        config={config}
        onConfigChange={setConfig}
        deviceValidated={deviceValidated}
        onValidateDevice={handleValidateDevice}
        isValidating={validateDeviceMutation.isPending}
      />

      <DescriptionInput
        value={config.description}
        onChange={(value) => setConfig({ ...config, description: value })}
        disabled={!deviceValidated}
        onGenerate={handleGenerate}
        onExecute={handleExecute}
        isGenerating={generateScriptMutation.isPending}
        generatedCode={generatedCode}
      />
    </div>
  );
}