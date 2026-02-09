import { useState } from 'react';
import { Plus, FolderOpen, MoreVertical, Trash2, Edit, RefreshCw, Calendar, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useProjects, useCreateProject, useDeleteProject, useIndexProjectLibrary } from '@/hooks/useApi';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

export function ProjectsView() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    library_path: '',
  });
  
  const { data: projects, isLoading, error, refetch } = useProjects();
  const createProjectMutation = useCreateProject();
  const deleteProjectMutation = useDeleteProject();
  const indexLibraryMutation = useIndexProjectLibrary();
  const { toast } = useToast();

  const handleCreate = async () => {
    if (!newProject.name || !newProject.library_path) {
      toast({
        title: 'Validation Error',
        description: 'Name and library path are required.',
        variant: 'destructive',
      });
      return;
    }

    try {
      await createProjectMutation.mutateAsync(newProject);
      toast({
        title: 'Project Created',
        description: `${newProject.name} has been created successfully.`,
      });
      setNewProject({ name: '', description: '', library_path: '' });
      setIsCreateOpen(false);
    } catch (err) {
      toast({
        title: 'Creation Failed',
        description: err instanceof Error ? err.message : 'Failed to create project.',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (id: string, name: string) => {
    try {
      await deleteProjectMutation.mutateAsync(id);
      toast({
        title: 'Project Deleted',
        description: `${name} has been removed.`,
      });
    } catch (err) {
      toast({
        title: 'Deletion Failed',
        description: err instanceof Error ? err.message : 'Failed to delete project.',
        variant: 'destructive',
      });
    }
  };

  const handleIndex = async (id: string, name: string) => {
    try {
      const result = await indexLibraryMutation.mutateAsync(id);
      toast({
        title: 'Library Indexed',
        description: `${name}: ${result.methods_indexed} methods indexed for RAG.`,
      });
      refetch();
    } catch (err) {
      toast({
        title: 'Indexing Failed',
        description: err instanceof Error ? err.message : 'Failed to index library.',
        variant: 'destructive',
      });
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="h-8 w-48 bg-muted animate-pulse rounded" />
          <div className="h-10 w-32 bg-muted animate-pulse rounded" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 bg-muted animate-pulse rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 flex items-center justify-center h-[calc(100vh-8rem)]">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto">
            <FolderOpen className="w-8 h-8 text-destructive" />
          </div>
          <h2 className="text-xl font-semibold text-foreground">Failed to Load Projects</h2>
          <p className="text-muted-foreground">Is the backend running?</p>
          <Button onClick={() => refetch()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Projects</h2>
          <p className="text-muted-foreground">Manage your automation projects and library paths</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Project
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Project</DialogTitle>
              <DialogDescription>
                Set up a new automation project with its enterprise library path.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Project Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., Mobile Banking App"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Brief description of the project..."
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="library_path">Enterprise Library Path</Label>
                <Input
                  id="library_path"
                  placeholder="e.g., /path/to/enterprise_lib"
                  value={newProject.library_path}
                  onChange={(e) => setNewProject({ ...newProject, library_path: e.target.value })}
                />
                <p className="text-xs text-muted-foreground">
                  Path to your automation library containing reusable test methods.
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={createProjectMutation.isPending}>
                {createProjectMutation.isPending ? 'Creating...' : 'Create Project'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Projects Grid */}
      {projects?.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 border-2 border-dashed border-border rounded-xl">
          <FolderOpen className="w-12 h-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No Projects Yet</h3>
          <p className="text-muted-foreground mb-4">Create your first project to get started</p>
          <Button onClick={() => setIsCreateOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Project
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects?.map((project) => (
            <div
              key={project.id}
              className="glass-card p-5 space-y-4 hover:border-primary/30 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <FolderOpen className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground">{project.name}</h3>
                    <p className="text-xs text-muted-foreground line-clamp-1">
                      {project.description || 'No description'}
                    </p>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => handleIndex(project.id, project.name)}>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Re-index Library
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Edit className="w-4 h-4 mr-2" />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={() => handleDelete(project.id, project.name)}
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <code className="bg-muted px-2 py-1 rounded text-xs truncate flex-1">
                    {project.library_path}
                  </code>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-border">
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Calendar className="w-3 h-3" />
                  <span>{format(new Date(project.created_at), 'MMM d, yyyy')}</span>
                </div>
                {project.last_indexed_at && (
                  <div className="flex items-center gap-1 text-xs text-success">
                    <Check className="w-3 h-3" />
                    <span>Indexed</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
