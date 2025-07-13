// frontend/src/components/ResearchForm.js
import React, { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  Select,
  Textarea,
  VStack,
  Heading,
  Text,
  useToast,
} from '@chakra-ui/react';
import { submitResearch } from '../services/api';

const ResearchForm = ({ onResearchStarted }) => {
  const [formData, setFormData] = useState({
    research_question: '',
    depth: 'standard',
    format: 'report',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const toast = useToast();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await submitResearch(formData);
      toast({
        title: 'Research started',
        description: `Research ID: ${response.research_id}`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      onResearchStarted(response.research_id);
    } catch (error) {
      toast({
        title: 'Error starting research',
        description: error.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box p={6} borderWidth="1px" borderRadius="lg" bg="white" shadow="md">
      <Heading as="h2" size="lg" mb={4}>
        Research Assistant Crew
      </Heading>
      <Text mb={6} color="gray.600">
        Enter your research question and our AI agents will work together to provide you with a comprehensive answer.
      </Text>
      
      <form onSubmit={handleSubmit}>
        <VStack spacing={4} align="stretch">
          <FormControl isRequired>
            <FormLabel>Research Question</FormLabel>
            <Textarea
              name="research_question"
              value={formData.research_question}
              onChange={handleChange}
              placeholder="Enter your research question here..."
              size="lg"
              rows={4}
            />
          </FormControl>

          <FormControl>
            <FormLabel>Research Depth</FormLabel>
            <Select name="depth" value={formData.depth} onChange={handleChange}>
              <option value="quick">Quick (5 min)</option>
              <option value="standard">Standard (15 min)</option>
              <option value="deep">Deep (30+ min)</option>
            </Select>
          </FormControl>

          <FormControl>
            <FormLabel>Output Format</FormLabel>
            <Select name="format" value={formData.format} onChange={handleChange}>
              <option value="report">Full Report</option>
              <option value="summary">Executive Summary</option>
              <option value="bullet_points">Bullet Points</option>
            </Select>
          </FormControl>

          <Button
            mt={4}
            colorScheme="blue"
            isLoading={isSubmitting}
            type="submit"
            size="lg"
          >
            Start Research
          </Button>
        </VStack>
      </form>
    </Box>
  );
};

export default ResearchForm;