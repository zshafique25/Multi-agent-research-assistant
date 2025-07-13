// frontend/src/components/ResearchResults.js
import React from 'react';
import {
  Box,
  Heading,
  Text,
  VStack,
  Link,
  Button,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  UnorderedList,
  ListItem,
  useClipboard,
  useToast,
} from '@chakra-ui/react';
import { ExternalLinkIcon, CopyIcon, DownloadIcon } from '@chakra-ui/icons';
import ReactMarkdown from 'react-markdown';

const ResearchResults = ({ result }) => {
  const { hasCopied, onCopy } = useClipboard(result?.report || '');
  const toast = useToast();

  if (!result) {
    return null;
  }

  const handleDownload = () => {
    const element = document.createElement('a');
    const file = new Blob([result.report], { type: 'text/markdown' });
    element.href = URL.createObjectURL(file);
    element.download = 'research_report.md';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

    toast({
      title: 'Report downloaded',
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };

  return (
    <Box p={6} borderWidth="1px" borderRadius="lg" bg="white" shadow="md">
      <VStack spacing={4} align="stretch">
        <Heading as="h2" size="lg">
          Research Results
        </Heading>

        <Tabs variant="enclosed" colorScheme="blue">
          <TabList>
            <Tab>Summary</Tab>
            <Tab>Full Report</Tab>
            <Tab>Sources</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>
              <Box p={4} borderWidth="1px" borderRadius="md" bg="gray.50">
                <ReactMarkdown>{result.summary}</ReactMarkdown>
              </Box>
            </TabPanel>

            <TabPanel>
              <Box mb={4}>
                <Button leftIcon={<CopyIcon />} onClick={onCopy} mr={2} size="sm">
                  {hasCopied ? 'Copied!' : 'Copy'}
                </Button>
                <Button leftIcon={<DownloadIcon />} onClick={handleDownload} size="sm">
                  Download
                </Button>
              </Box>

              <Box p={4} borderWidth="1px" borderRadius="md" bg="gray.50" maxH="60vh" overflowY="auto">
                <ReactMarkdown>{result.report}</ReactMarkdown>
              </Box>
            </TabPanel>

            <TabPanel>
              <UnorderedList spacing={2}>
                {result.sources.map((source, index) => (
                  <ListItem key={index}>
                    <Link href={source.url} isExternal color="blue.600">
                      {source.title} <ExternalLinkIcon mx="2px" />
                    </Link>
                  </ListItem>
                ))}
              </UnorderedList>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Box>
  );
};

export default ResearchResults;